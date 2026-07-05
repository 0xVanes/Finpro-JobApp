import streamlit as st
from menu import menu_with_redirect
import os
from dotenv import find_dotenv
import requests

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Career Path", layout="wide")

# Load menu
menu_with_redirect()

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="career-header">
  <div class="emoji-bg">🛤️</div>
  <h1>Career Path Visualizer</h1>
  <p class="sub">Peta jalur karir</p>
  <div class="badge-row">
    <span>Visualisasi jalur (FR-5.01)</span>
  </div>
</div>
""", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)
# ambil data dari CV no,3
## Webhook CV
find_dotenv()
roadmap_url = os.environ.get("CV_WEBHOOK_URL")
response = requests.post(roadmap_url, json={})
if response.status_code != 200:
    st.error("Failed to connect to n8n")
    st.stop()
data = response.json()

candidate_profile = data["candidate_profile"]
target = candidate_profile["current_role"]
target= candidate_profile["current_role"]
with col1:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">📊</div>
    <h3 class="career-title">Job Exp</h3>
    <div class="career-job">{target}</div>
</div>""", unsafe_allow_html=True)

exp = candidate_profile["experience_years"]
if exp <= 2:
    level = "Junior"
elif exp <= 5:
    level = "Mid-Level"
else:
    level = "Senior"
## 0-2 Junior, 3-5 Mid, 6+ Senior   
with col2:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">🎯</div>
    <h3 class="career-title">Job Level</h3>
    <div class="career-job">{level}</div>
</div>""", unsafe_allow_html=True)

career_roadmap = data["career_roadmap"]
phases = career_roadmap["phases"]
phase_names = " → ".join([p["phase"] for p in phases])
with col3:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">📈</div>
    <h3 class="career-title">3 tahap</h3>
    <div class="career-job">{phase_names}</div>
</div>""", unsafe_allow_html=True)

## ISI DARI Hasil LLM
st.markdown(f"""<div class="salary-info">💡 Jalur Karir menuju: {career_roadmap["target_career"]} </div>""", unsafe_allow_html=True)