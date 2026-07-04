import streamlit as st
import requests
import pandas as pd
from menu import menu_with_redirect
from pathlib import Path
import plotly.express as px
import re
from dotenv import load_dotenv
import pymysql
import os

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

# Load menu
menu_with_redirect()

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

## connect ke SQL
load_dotenv()
def get_connection(timeout=10):
    try:
        connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=pymysql.cursors.DictCursor,
        db= os.environ.get("MYSQL_DATABASE"),
        host= os.environ.get("MYSQL_HOST"),
        password= os.environ.get("MYSQL_PASSWORD"),
        read_timeout=timeout,
        port= 25615,
        user= os.environ.get("MYSQL_USER"),
        write_timeout=timeout,)
        return connection

    except Exception as e:
        print(f"[SQL] Connection failed: {e}")

conn = get_connection()
if conn:
  print("SQL is Connected")
cursor = conn.cursor()

## fetch hot demand
query = """SELECT job_title AS skill, COUNT(*) AS demand
FROM jobs
GROUP BY job_title
ORDER BY demand DESC
LIMIT 7;"""
cursor.execute(query)
rows = cursor.fetchall()

## HOT DEMAND SKILLS
skill_counts = pd.DataFrame(rows).copy()
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
## fetch distribusi gaji
query = """SELECT job_title, salary_max
FROM jobs
WHERE salary_max IS NOT NULL
ORDER BY salary_max DESC
LIMIT 4;"""
cursor.execute(query)
rows = cursor.fetchall()

salary_df = pd.DataFrame(rows).copy()
salary_df = salary_df[salary_df["salary_max"] != "None"]
salary_df["salary_num"] = salary_df["salary_max"]
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
top6 = skill_counts.head(6).copy()
top6.columns = ["skill", "demand"]

def status(x):
    if x >= 20:
        return "Tinggi"
    elif x >=10:
        return "Sedang"
    else:
        return "Rendah"
top6["Status"] = top6["demand"].apply(status)
st.dataframe(top6)