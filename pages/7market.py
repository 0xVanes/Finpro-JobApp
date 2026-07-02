import streamlit as st
import requests
import pandas as pd
from menu import menu_with_redirect
from pathlib import Path
import plotly.express as px
import re

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

# Load menu
menu_with_redirect()

# Load N8N Webhook URL
n8n_hotdemand_url = "https://n8n-student.purwadhika.com/webhook/7-market-hotdemand"
n8n_gaji_url = "https://n8n-student.purwadhika.com/webhook/7-market-distribusigaji"

def fetch_n8n_hotdemand_data():
    response = requests.post(n8n_hotdemand_url)
    if response.status_code == 200:
        data1 = response.json()
        return pd.DataFrame(data1)
    else:
        st.error("Failed to fetch data from n8n")
        return pd.DataFrame()
df1 = fetch_n8n_hotdemand_data()
    
def fetch_n8n_gaji_data():
    response = requests.post(n8n_gaji_url)
    if response.status_code == 200:
        data2 = response.json()
        return pd.DataFrame(data2)
    else:
        st.error("Failed to fetch data from n8n")
        return pd.DataFrame()
df2 = fetch_n8n_gaji_data()

# Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## ------- Frontend STARTS HERE
st.markdown("""
<div class="market-header">
  <div class="emoji-bg">📊</div>
  <h1>Market Insight</h1>
  <p class="sub">Statistik pasar kerja Indonesia dari 473 data nyata</p>
  <div class="badge-row">
    <span>Hot Demand (FR-7.01)</span>
    <span>Distribusi Gaji (FR-7.02)</span>
    <span>SQL Agent</span>
  </div>
</div>
""", unsafe_allow_html=True)

## Nanti ini dihapus ganti SQL atau ga usah?
base_dir = Path(__file__).resolve().parent.parent
data_path = base_dir / "dataset" / "jobs.jsonl"
df = pd.read_json(data_path, lines=True)

### HOT DEMAND SKILLS
skill_counts = (df["job_title"].value_counts().head(7).reset_index())
skill_counts.columns = ["skill", "demand"]

fig = px.bar(skill_counts.sort_values("demand"),
    x="demand", y="skill", orientation="h", text="demand")

colors = [ "#7C6CFF","#766FFB", "#7073F7", "#6A78F3", "#6380EE", "#5E92E7", "#59D6D6"]
fig.update_traces( textposition="outside", marker_color=colors)
fig.update_layout( height=420,
    showlegend=False, xaxis_title="", yaxis_title="",
    xaxis=dict(showgrid=False, visible=False),
    yaxis=dict(showgrid=False),
    margin=dict(l=10, r=20, t=20, b=10))

st.subheader("🔥 HOT DEMAND SKILLS (FR-7.01)")
st.plotly_chart(fig, use_container_width=True)

st.divider()

### DISTRIBUSI GAJI RATA-RATA
# nanti dihapus diganti sama SQL
salary_df = df[df["salary"].notna()].copy()
salary_df = salary_df[salary_df["salary"] != "None"]

def extract_salary(text):
    nums = re.findall(r"\d[\d.,]*", str(text))
    if len(nums) == 0:
        return None
    value = nums[0].replace(".", "").replace(",", "")

    try:
        return int(value)
    except:
        return None

salary_df["salary_num"] = salary_df["salary"].apply(extract_salary)
salary_df = (salary_df.dropna(subset=["salary_num"]).sort_values("salary_num", ascending=False).head(4))

st.write("💰 DISTRIBUSI GAJI RATA-RATA PER BIDANG (FR-7.02)")
cols = st.columns(2)
for i, (_, row) in enumerate(salary_df.iterrows()):
    with cols[i % 2]:
      st.markdown(f"""<div class="salary-card">
    <div class="salary-icon">💻</div>
    <h3 class="salary-title">Rp {row['salary_num']:,}</h3>
    <div class="salary-job">{row['job_title']}</div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="salary-info">💡 Posisi dengan gaji tertinggi adalah
<b>{salary_df.iloc[0]['job_title']}</b> Rp {salary_df.iloc[0]['salary_num']:,}.
</div>""", unsafe_allow_html=True)
st.divider()

### Table Demand
top6 = (df["job_title"].value_counts().head(6).reset_index())
top6.columns = ["Skill", "Demand"]

def status(x):
    if x >= 20:
        return "Tinggi"
    elif x >=10:
        return "Sedang"
    else:
        return "Rendah"
top6["Status"] = top6["Demand"].apply(status)
st.table(top6)