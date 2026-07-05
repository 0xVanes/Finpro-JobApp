import streamlit as st
import os
from dotenv import find_dotenv
from menu import menu_with_redirect
import requests

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - SkillGAP", layout="wide")

# Load menu
menu_with_redirect()

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## Webhook n8n
find_dotenv()
N8N_URL = os.environ.get("CV_WEBHOOK_URL")
response = requests.post(N8N_URL, json={})

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="career-header">
  <div class="emoji-bg">🛤️</div>
  <h1>Skill Gap</h1>
  <p class="sub">Gap skill + link sertifikasi spesifik</p>
  <div class="badge-row">
    <span>Gap analysis (FR-5.02)</span>
    <span>Link belajar (FR-5.04)</span>
  </div>
</div>
""", unsafe_allow_html=True)

## Peta Jalur Karir (FR-5.01)
st.write("PETA JALUR KARIR (FR-5.01)")
response = requests.post(N8N_URL, json={})
if response.status_code != 200:
    st.error("Failed to connect to n8n")
    st.stop()

data = response.json()
gap_data = data["gap_analysis"]["careers"]
certifications = data["certifications"]["recommendations"]

cols = st.columns(min(3, len(gap_data)))

for i, item in enumerate(gap_data[:3]):

    gap_html = ""

    for skill in item["missing_skills"]:
        gap_html += f"""
        <span class="skill-pill">
            {skill["skill"]} ({skill["priority"]})
        </span>
        """

    existing_html = ""

    for skill in item["existing_skills"]:
        existing_html += f"""
        <span class="skill-pill">{skill}</span>
        """

    with cols[i]:
        st.markdown(f"""
        <div class="skill-card">
            <div class="skill-badge">{item["career"]}</div>
            <div class="skill-count">{len(item["missing_skills"])} Skill Gaps</div>

            <div class="skill-gap-title">GAP (FR-5.02)</div>
            <div>{gap_html}</div>
        </div>""", unsafe_allow_html=True)

## 📚 LINK BELAJAR & SERTIFIKASI (FR-5.04)
for rec in certifications:
    links_html = ""
    for course in rec["courses"]:
        badge = "🆓" if course["free"] else "💰"
        links_html += f"""
        <a href="{course['url']}"
           target="_blank"
           class="learn-pill">
           {badge} {course['provider']}
        </a>"""
    st.markdown(f"""
    <div class="learning-card">
        <div class="learning-header">
            <h4>{rec["skill"]}</h4>
            <div class="priority-pill">Skill Gap</div>
        </div>
        <div class="learning-links">{links_html}</div>
    </div>
    """, unsafe_allow_html=True)