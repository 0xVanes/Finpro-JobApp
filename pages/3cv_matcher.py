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

## --- Session state init ---
if "cv_result" not in st.session_state:
    st.session_state.cv_result = None
if "selected_job_idx" not in st.session_state:
    st.session_state.selected_job_idx = None
if "analyzed_filename" not in st.session_state:
    st.session_state.analyzed_filename = None

analyze_clicked = st.button("✨ Analisis & Rekomendasikan", use_container_width=True)

# Reset selection + cache result saat file baru di upload
if uploaded.name != st.session_state.analyzed_filename:
    st.session_state.cv_result = None
    st.session_state.selected_job_idx = None

if analyze_clicked:
    # ── Ekstraksi CV ─────────────────────────────────────────────────
    with st.spinner("Membaca CV..."):
        cv_text = extract_cv_text(uploaded)

    if not cv_text.strip():
        show_error(
            "Gagal membaca teks dari CV. "
            "Pastikan file tidak terenkripsi, terlindungi password, atau kosong."
        )
        st.stop()

    with st.spinner("AI menganalisis CV, mencari lowongan, dan menyusun jalur karir..."):
        result = call_n8n(
            payload={"mode": "cv_match", "cv_text": cv_text, "top_n": 3},
            timeout=TIMEOUT_CV,
        )

    if "error" in result:
        show_error(result["error"])
        st.stop()

    st.session_state.cv_result = result
    st.session_state.analyzed_filename = uploaded.name
    st.session_state.selected_job_idx = None  # reset untuk analisis baru

# Belum upload cv
if st.session_state.cv_result is None:
    st.stop()

result = st.session_state.cv_result

# ═══════════════════════════════════════════════════════════════
# BAGIAN 1 — TOP 3 REKOMENDASI LOWONGAN
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

# FR-4.03, FR-4.04 & FR-5.01: Top 3 rekomendasi lowongan

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

        is_selected = st.session_state.selected_job_idx == rank
        card_style = "border: 2px solid #6D5DF6;" if is_selected else ""

        st.markdown(
            f'<div class="job-card" style="{card_style}">'
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

        btn_col, _ = st.columns([1, 3])
        with btn_col:
            btn_label = "✅ Terpilih" if is_selected else "Pilih Lowongan Ini"
            if st.button(btn_label, key=f"select_job_{rank}", use_container_width=True):
                st.session_state.selected_job_idx = rank
                st.rerun()

        st.write("")
else:
    st.warning(
        "Tidak ada rekomendasi lowongan yang ditemukan. "
        "Pastikan CV memuat informasi skill dan pengalaman."
    )

# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — SERTIFIKASI & LINK BELAJAR (FR-5.04) UNTUK LOWONGAN YANG TERPILIH
# ═════════════════════════════════════════════════════════════════════════════

certifications = result.get("certifications", [])

if st.session_state.selected_job_idx is None:
    section_lbl("Skill Gap(FR-5.02 - 5.05)", "👤")
    
    if recommendations:
        st.info("👆 Pilih salah satu lowongan di atas untuk melihat rekomendasi sertifikasi dan link belajar yang relevan.")
else:
    selected_rec = recommendations[st.session_state.selected_job_idx - 1]
    selected_missing_skills = {
        s.strip().lower() for s in selected_rec.get("missing_skills", [])
    }

    relevant_certifications = [
        cert for cert in certifications
        if cert.get("skill", "").strip().lower() in selected_missing_skills
    ]

    if relevant_certifications:
        section_lbl(
            f"Rekomendasi Link Belajar & Sertifikasi untuk \"{selected_rec.get('job_title', 'N/A')}\" (FR-5.04)",
            "📚"
        )

        for rec in relevant_certifications:
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
    else:
        st.info(
            f"Tidak ditemukan rekomendasi sertifikasi untuk skill gap pada "
            f"\"{selected_rec.get('job_title', 'N/A')}\"."
        )

# ═══════════════════════════════════════════════════════════════
# BAGIAN 3 — CAREER ROADMAP UNTUK LOWONGAN YANG TERPILIH
# ═══════════════════════════════════════════════════════════════

career_roadmaps = result.get("career_roadmap", [])

if st.session_state.selected_job_idx is None:
    if recommendations:
        None
else:
    selected_rec = recommendations[st.session_state.selected_job_idx - 1]

    career_roadmap = next(
        (
            rm for rm in career_roadmaps
            if rm.get("job_title") == selected_rec.get("job_title")
            and rm.get("company_name") == selected_rec.get("company_name")
        ),
        {}
    )

    phases = career_roadmap.get("phases", [])

    if phases:
        section_lbl(
            f"Roadmap Menuju {career_roadmap.get('target_career', selected_rec.get('job_title', 'Karir Target'))}",
            "🗺️"
        )

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
    else:
        st.info(
            f"Tidak ditemukan roadmap karir untuk "
            f"\"{selected_rec.get('job_title', 'N/A')}\" di \"{selected_rec.get('company_name', 'N/A')}\"."
        )
