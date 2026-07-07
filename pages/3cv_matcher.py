import streamlit as st
import requests
from dotenv import find_dotenv
from menu import menu_with_redirect
import json

from utils import (
    call_n8n, section_lbl, show_error,
    extract_cv_text, validate_cv_upload, render_skill_chips, TIMEOUT_CV,
)

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - CV Matcher", layout="wide")

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
<div class="cvmatcher-header">
  <div class="emoji-bg">📄</div>
  <h1>CV Matcher</h1>
  <p class="sub">Upload CV → Top 3 lowongan paling cocok beserta alasan spesifik</p>
  <div class="badge-row">
    <span>Upload PDF/DOCX (FR-4.01)</span>
    <span>Top 3 (FR-4.03)</span>
    <span>Hanya di memory (NFR-5.01)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# FR-4.01: File uploader
uploaded = st.file_uploader(
    "Upload CV kamu (PDF atau DOCX) — tidak disimpan permanen (NFR-5.01)",
    type=["pdf", "docx"],
    help="Maksimal 10 MB. File hanya diproses di memory selama sesi ini.",
)

if uploaded is None:
    st.info("Upload CV kamu untuk mendapatkan rekomendasi lowongan yang paling cocok.")
    st.stop()

# Validasi file sebelum diproses
is_valid, error_msg = validate_cv_upload(uploaded)
if not is_valid:
    show_error(error_msg)
    st.stop()

if not st.button("✨ Analisis & Rekomendasikan", use_container_width=True):
    st.stop()

# ── Ekstraksi CV ─────────────────────────────────────────────────
with st.spinner("Membaca CV..."):
    cv_text = extract_cv_text(uploaded)

if not cv_text.strip():
    show_error(
        "Gagal membaca teks dari CV. "
        "Pastikan file tidak terenkripsi, terlindungi password, atau kosong."
    )
    st.stop()

# ── Kirim ke N8N ─────────────────────────────────────────────────
with st.spinner("AI mencocokkan profil dengan 473 lowongan..."):
    result = call_n8n(
        payload={"mode": "cv_match", "cv_text": cv_text, "top_n": 3},
        timeout=TIMEOUT_CV,     # NFR-2.03: maksimal 30 s
    )

if "error" in result:
    show_error(result["error"])
    st.stop()
# FR-4.02: Profil kandidat yang terdeteksi
if "output" in result:
    result = json.loads(result["output"])

profile = result.get("candidate_profile", {})
if profile:
    section_lbl("Profil Terdeteksi (FR-4.02)", "👤")
    c1, c2, c3 = st.columns(3)
    c1.metric("Posisi",      profile.get("current_role", "—"))
    c2.metric("Pengalaman",  f"{profile.get('experience_years', 0)} thn")
    c3.metric("Skill",       str(len(profile.get("key_skills", []))))

    key_skills = profile.get("key_skills", [])
    if key_skills:
        skill_chips = "".join(
            f'<span class="chip has">{s}</span>' for s in key_skills
        )
        st.markdown(skill_chips, unsafe_allow_html=True)
    st.write("")

# FR-4.03: Top 3 rekomendasi
recommendations = result.get("recommendations", [])[:3]

if not recommendations:
    st.warning(f"""Tidak ada rekomendasi yang ditemukan.
        Pastikan CV memuat informasi skill dan pengalaman {parsed}"""
    )
    st.stop()

section_lbl("Top 3 Rekomendasi (FR-4.03)", "🏆")

for rank, rec in enumerate(recommendations, start=1):
    match_pct = rec.get("match_percentage", 0)
    job_title = rec.get("job_title", "N/A")
    company   = rec.get("company_name", "N/A")
    location  = rec.get("location", "N/A")
    advice    = rec.get("advice", "")
    matching  = rec.get("matching_skills", [])
    missing   = rec.get("missing_skills", [])

    st.markdown(
        f'<div class="job-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div>'
        f'<div style="font-size:.7rem;color:#6D5DF6;font-weight:700">#{rank}</div>'
        f'<h3>{job_title}</h3>'
        f'</div>'
        f'<span class="match-tag">{match_pct}% match</span>'
        f'</div>'
        f'<div class="job-company">{company}</div>'
        f'<div class="job-meta">📍 {location}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Chip skill
    render_skill_chips(matching, missing)

    # FR-4.04: Alasan rekomendasi
    if advice:
        st.markdown(
            f'<div class="job-reason">💡 FR-4.04: {advice}</div>',
            unsafe_allow_html=True,
        )
    st.write("")

## Career Path
col1, col2, col3 = st.columns(3)
candidate_profile = result["candidate_profile"]
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

career_roadmap = result.get("career_roadmap", {})
if not career_roadmap:
    st.warning("Career roadmap not available yet — try again in a moment.")
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


## Peta Jalur Karir (FR-5.01)
st.write("PETA JALUR KARIR (FR-5.01)")
gap_data = result["gap_analysis"]["careers"]
certifications = result["certifications"]["recommendations"]

cols = st.columns(int(min(3, len(gap_data))))

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