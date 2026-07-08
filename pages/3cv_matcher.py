import streamlit as st
from menu import menu_with_redirect

from utils import (
    call_n8n, section_lbl, show_error, load_css,
    extract_cv_text, validate_cv_upload, render_skill_chips, TIMEOUT_CV,
)

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - CV Matcher", layout="wide")

# Load menu
menu_with_redirect()

load_css()

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="cvmatcher-header">
  <div class="emoji-bg">📄</div>
  <h1>CV Matcher</h1>
  <p class="sub">Upload CV → lowongan tercocok, jalur karir, dan skill gap sekaligus</p>
  <div class="badge-row">
    <span>Upload PDF/DOCX (FR-4.01)</span>
    <span>Top 3 Lowongan (FR-4.03)</span>
    <span>Career Path (FR-5.01)</span>
    <span>Skill Gap (FR-5.02)</span>
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
    st.info("Upload CV kamu untuk mendapatkan rekomendasi lowongan, jalur karir, dan skill gap.")
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

# ── SATU panggilan ke N8N untuk SEMUA section ─────────────────────
# Workflow n8n (mode=cv_match) sekarang menjalankan berantai:
# CV Matcher Agent -> Career Path Classification -> Gap Analysis ->
# Recommend Certification -> Career Roadmap Generator, lalu
# menggabungkan semua hasilnya jadi satu response JSON.
with st.spinner("AI menganalisis CV, mencari lowongan, dan menyusun jalur karir..."):
    result = call_n8n(
        payload={"mode": "cv_match", "cv_text": cv_text, "top_n": 3},
        timeout=TIMEOUT_CV,
    )

if "error" in result:
    show_error(result["error"])
    st.stop()

# ═══════════════════════════════════════════════════════════════
# BAGIAN 1 — CV MATCHER (FR-4.02, FR-4.03, FR-4.04)
# ═══════════════════════════════════════════════════════════════

# FR-4.02: Profil kandidat yang terdeteksi
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

# FR-4.03 & FR-4.04: Top 3 rekomendasi lowongan
recommendations = result.get("recommendations", [])[:3]

if recommendations:
    section_lbl("Top 3 Rekomendasi Lowongan (FR-4.03)", "🏆")

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
        render_skill_chips(matching, missing)
        if advice:
            st.markdown(f'<div class="job-reason">💡 {advice}</div>', unsafe_allow_html=True)
        st.write("")
else:
    st.warning(
        "Tidak ada rekomendasi lowongan yang ditemukan. "
        "Pastikan CV memuat informasi skill dan pengalaman."
    )

# ═══════════════════════════════════════════════════════════════
# BAGIAN 2 — CAREER PATH (FR-5.01)
# ═══════════════════════════════════════════════════════════════

career_paths = result.get("career_paths", [])

if career_paths:
    st.divider()
    st.markdown("""
    <div class="career-header">
      <div class="emoji-bg">🛤️</div>
      <h1>Rekomendasi Career Path</h1>
      <p class="sub">5 jalur karir yang paling sesuai dengan profil CV kamu</p>
      <div class="badge-row">
        <span>Visualisasi jalur (FR-5.01)</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cp_cols = st.columns(min(5, len(career_paths)) or 1)
    for i, cp in enumerate(career_paths[:5]):
        with cp_cols[i % len(cp_cols)]:
            confidence = cp.get("confidence", 0)
            st.markdown(
                f'<div class="career-card">'
                f'<div class="career-icon">🎯</div>'
                f'<h3 class="career-title">{confidence}%</h3>'
                f'<div class="career-job">{cp.get("career", "N/A")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Alasan tiap rekomendasi (di bawah grid, supaya tidak terlalu sempit)
    with st.expander("Lihat alasan tiap rekomendasi career path"):
        for cp in career_paths[:5]:
            st.markdown(f"**{cp.get('career', 'N/A')}** ({cp.get('confidence', 0)}%) — {cp.get('reason', '—')}")

# ═══════════════════════════════════════════════════════════════
# BAGIAN 3 — SKILL GAP (FR-5.02)
# ═══════════════════════════════════════════════════════════════

gap_analysis = result.get("gap_analysis", [])

if gap_analysis:
    st.divider()
    st.markdown("""
    <div class="career-header">
      <div class="emoji-bg">🎯</div>
      <h1>Skill Gap</h1>
      <p class="sub">Skill yang perlu dikembangkan untuk tiap jalur karir</p>
      <div class="badge-row">
        <span>Gap analysis (FR-5.02)</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    gap_cols = st.columns(min(3, len(gap_analysis)) or 1)
    for i, item in enumerate(gap_analysis[:3]):
        missing_skills = item.get("missing_skills", [])
        existing_skills = item.get("existing_skills", [])

        gap_html = "".join(
            f'<span class="skill-pill">{skill.get("skill", "?")} ({skill.get("priority", "—")})</span>'
            for skill in missing_skills
        )

        with gap_cols[i % len(gap_cols)]:
            st.markdown(
                f'<div class="skill-card">'
                f'<div class="skill-badge">{item.get("career", "N/A")}</div>'
                f'<div class="skill-count">{len(missing_skills)} Skill Gaps</div>'
                f'<div class="skill-jobs">✓ Sudah dikuasai: {", ".join(existing_skills) or "—"}</div>'
                f'<div class="skill-gap-title">GAP (FR-5.02)</div>'
                f'<div>{gap_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════
# BAGIAN 4 — SERTIFIKASI & LINK BELAJAR (FR-5.04)
# ═══════════════════════════════════════════════════════════════

certifications = result.get("certifications", [])

if certifications:
    section_lbl("Rekomendasi Link Belajar & Sertifikasi (FR-5.04)", "📚")

    for rec in certifications:
        links_html = ""
        for course in rec.get("courses", []):
            badge = "🆓" if course.get("free") else "💰"
            links_html += (
                f'<a href="{course.get("url", "#")}" target="_blank" class="learn-pill">'
                f'{badge} {course.get("provider", "?")}</a>'
            )
        st.markdown(
            f'<div class="learning-card">'
            f'<div class="learning-header">'
            f'<h4>{rec.get("skill", "N/A")}</h4>'
            f'<div class="priority-pill">{rec.get("priority", "Skill Gap")}</div>'
            f'</div>'
            f'<div class="learning-links">{links_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════
# BAGIAN 5 — CAREER ROADMAP
# ═══════════════════════════════════════════════════════════════

career_roadmap = result.get("career_roadmap", {})
phases = career_roadmap.get("phases", [])

if phases:
    section_lbl(f"Roadmap Menuju {career_roadmap.get('target_career', 'Karir Target')}", "🗺️")

    roadmap_cols = st.columns(min(3, len(phases)) or 1)
    for i, phase in enumerate(phases[:3]):
        goals = phase.get("goals", [])
        goals_html = "".join(f'<div class="career-job">• {g}</div>' for g in goals)

        with roadmap_cols[i % len(roadmap_cols)]:
            st.markdown(
                f'<div class="career-card">'
                f'<div class="career-icon">📈</div>'
                f'<h3 class="career-title">{phase.get("phase", "—")}</h3>'
                f'{goals_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    if career_roadmap.get("summary"):
        st.markdown(
            f'<div class="salary-info">💡 {career_roadmap["summary"]}</div>',
            unsafe_allow_html=True,
        )
