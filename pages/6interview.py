"""
Simulasi Wawancara (Interview Agent) — FR-6.01 s/d FR-6.05.

Wawancara adaptif berbasis lowongan nyata + CV pengguna. State percakapan
disimpan di st.session_state; setiap giliran mengirim seluruh riwayat ke n8n
(webhook stateless). Panjang sesi ditentukan agen (field "done"), dengan
progress bar dari field "progress" yang dikirim agen.

Kontrak webhook & alur lengkap: lihat docs/interview.md.
"""

import streamlit as st
from menu import menu_with_redirect

from utils import (
    call_n8n, show_error, section_lbl, load_css,
    extract_cv_text, validate_cv_upload, build_interview_pdf,
    TIMEOUT_CHAT, TIMEOUT_CV, TIMEOUT_SQL,
)

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Interview", layout="wide")

# Load menu (auth-gated)
menu_with_redirect()
load_css()

# ── Header ───────────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
  <div class="emoji-bg">🎤</div>
  <h1>Simulasi Wawancara</h1>
  <p class="sub">Latihan interview untuk lowongan nyata, disesuaikan dengan CV kamu</p>
  <div class="badge-row">
    <span>Pilih lowongan nyata (FR-6.01)</span>
    <span>Tanya-jawab adaptif (FR-6.02)</span>
    <span>Verdict + PDF (FR-6.04 · FR-6.05)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Inisialisasi session_state ──────────────────────────────────
_IV_DEFAULTS = {
    "iv_stage":          "setup",   # "setup" | "running" | "done"
    "iv_cv_text":        "",
    "iv_cv_profile":     {},
    "iv_job":            {},         # {job_id, job_title, company_name, location}
    "iv_history":        [],         # [{question, answer, category}]
    "iv_current_q":      {},         # pertanyaan yang menunggu jawaban
    "iv_progress":       0,          # nilai progress tampil (setelah clamp)
    "iv_assessment":     {},
    "iv_search_results": [],         # cache hasil pencarian lowongan
}
for _key, _val in _IV_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = list(_val) if isinstance(_val, list) else (
            dict(_val) if isinstance(_val, dict) else _val
        )


def reset_interview() -> None:
    """Kembalikan semua state wawancara ke kondisi awal (untuk ulang sesi)."""
    for k, v in _IV_DEFAULTS.items():
        st.session_state[k] = list(v) if isinstance(v, list) else (
            dict(v) if isinstance(v, dict) else v
        )


def apply_progress(agent_progress: object, done: bool) -> None:
    """
    Terapkan progress dari agen dengan aturan tampil (lihat docs/interview.md):
    monotonik (tidak mundur) dan tidak pernah 100% sebelum done (maks 95%).
    """
    if done:
        st.session_state.iv_progress = 100
        return
    try:
        p = int(agent_progress)
    except (TypeError, ValueError):
        p = st.session_state.iv_progress
    st.session_state.iv_progress = min(max(st.session_state.iv_progress, p), 95)


def run_assessment() -> None:
    """Panggil action=assess dan simpan hasilnya, lalu pindah ke fase done."""
    with st.spinner("AI menilai keseluruhan wawancara..."):
        result = call_n8n(
            payload={
                "mode":       "interview",
                "action":     "assess",
                "job_id":     st.session_state.iv_job.get("job_id"),
                "cv_profile": st.session_state.iv_cv_profile,
                "history":    st.session_state.iv_history,
            },
            timeout=TIMEOUT_CV,
        )
    if "error" in result:
        show_error(result["error"])
        return
    st.session_state.iv_assessment = result
    st.session_state.iv_progress = 100
    st.session_state.iv_stage = "done"
    st.rerun()


# ════════════════════════════════════════════════════════════════
# FASE 1 — SETUP (FR-6.01)
# ════════════════════════════════════════════════════════════════
if st.session_state.iv_stage == "setup":

    # ── Langkah 1: Upload CV ─────────────────────────────────────
    section_lbl("1. Upload CV kamu (FR-4.01)", "📄")
    uploaded = st.file_uploader(
        "CV (PDF atau DOCX) — tidak disimpan permanen (NFR-5.01)",
        type=["pdf", "docx"],
        help="Pertanyaan wawancara disusun berdasarkan isi CV ini dan lowongan yang dipilih.",
    )

    # ── Langkah 2: Cari & pilih lowongan nyata ───────────────────
    section_lbl("2. Cari lowongan yang ingin dilatih (FR-6.01)", "🔍")
    col_kw, col_btn = st.columns([3, 1])
    with col_kw:
        keyword = st.text_input(
            "Posisi / kata kunci",
            placeholder="Data Analyst",
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button("🔍 Cari", use_container_width=True)

    if search_clicked:
        if not keyword.strip():
            st.warning("Ketik posisi atau kata kunci dulu.")
        else:
            with st.spinner("Mencari lowongan..."):
                result = call_n8n(
                    payload={
                        "mode":        "search",
                        "keyword":     keyword.strip(),
                        "work_type":   None,
                        "city":        None,
                        "salary_min":  None,
                        "hybrid_only": False,
                    },
                    timeout=TIMEOUT_SQL,
                )
            if "error" in result:
                show_error(result["error"])
                st.session_state.iv_search_results = []
            else:
                st.session_state.iv_search_results = result.get("jobs", [])

    # Tampilkan hasil pencarian untuk dipilih
    results = st.session_state.iv_search_results
    selected_job = None
    if results:
        # Peringatkan bila kontrak job_id belum dipenuhi workflow n8n
        if any(not j.get("job_id") for j in results):
            st.warning(
                "Sebagian lowongan tidak memiliki `job_id`. Pastikan workflow n8n "
                "menyertakan `job_id` di tiap hasil pencarian (lihat docs/interview.md)."
            )

        st.caption(f"Ditemukan {len(results)} lowongan — pilih satu:")
        idx = st.radio(
            "Pilih lowongan",
            options=list(range(len(results))),
            format_func=lambda i: (
                f"{results[i].get('job_title', 'N/A')} — "
                f"{results[i].get('company_name', 'N/A')} "
                f"({results[i].get('location', 'N/A')})"
            ),
            label_visibility="collapsed",
        )
        selected_job = results[idx]
    else:
        st.info("Cari lowongan di atas, lalu pilih satu untuk memulai wawancara.")

    # ── Langkah 3: Mulai wawancara ───────────────────────────────
    st.divider()
    start_clicked = st.button("🎤 Mulai Wawancara", use_container_width=True, type="primary")

    if start_clicked:
        # Validasi prasyarat
        if uploaded is None:
            show_error("Upload CV dulu sebelum memulai wawancara.")
            st.stop()
        is_valid, err = validate_cv_upload(uploaded)
        if not is_valid:
            show_error(err)
            st.stop()
        if selected_job is None:
            show_error("Cari dan pilih satu lowongan dulu.")
            st.stop()
        if not selected_job.get("job_id"):
            show_error("Lowongan terpilih tidak memiliki job_id — tidak bisa memulai wawancara.")
            st.stop()

        # Ekstraksi CV
        with st.spinner("Membaca CV..."):
            cv_text = extract_cv_text(uploaded)
        if not cv_text.strip():
            show_error(
                "Gagal membaca teks dari CV. Pastikan file tidak terenkripsi, "
                "terlindungi password, atau kosong."
            )
            st.stop()

        # Panggil action=start → pertanyaan pertama
        with st.spinner("AI menyiapkan pertanyaan pertama..."):
            result = call_n8n(
                payload={
                    "mode":     "interview",
                    "action":   "start",
                    "cv_text":  cv_text,
                    "job_id":   selected_job["job_id"],
                    "position": selected_job.get("job_title", ""),
                },
                timeout=TIMEOUT_CHAT,
            )
        if "error" in result:
            show_error(result["error"])
            st.stop()

        # Simpan state & pindah ke fase running
        st.session_state.iv_cv_text    = cv_text
        st.session_state.iv_cv_profile = result.get("cv_profile", {})
        st.session_state.iv_job        = {
            "job_id":       selected_job["job_id"],
            "job_title":    selected_job.get("job_title", "N/A"),
            "company_name": selected_job.get("company_name", "N/A"),
            "location":     selected_job.get("location", "N/A"),
        }
        st.session_state.iv_current_q = {
            "question":        result.get("question", ""),
            "category":        result.get("category", ""),
            "question_number": result.get("question_number", 1),
        }
        st.session_state.iv_history = []
        apply_progress(result.get("progress", 0), done=False)
        st.session_state.iv_stage = "running"
        st.rerun()


# ════════════════════════════════════════════════════════════════
# FASE 2 — RUNNING (FR-6.02, FR-6.03)
# ════════════════════════════════════════════════════════════════
elif st.session_state.iv_stage == "running":

    job = st.session_state.iv_job
    st.caption(
        f"🎯 Wawancara untuk **{job.get('job_title', '-')}** "
        f"di {job.get('company_name', '-')}"
    )

    # Progress bar (nilai sudah di-clamp saat disimpan)
    pct = st.session_state.iv_progress
    q_no = len(st.session_state.iv_history) + 1
    st.progress(pct / 100, text=f"Progres wawancara: {pct}%  ·  Pertanyaan ke-{q_no}")

    # Riwayat Q&A yang sudah dijawab
    for i, turn in enumerate(st.session_state.iv_history, start=1):
        with st.chat_message("assistant"):
            cat = turn.get("category", "")
            st.markdown(f"**Pertanyaan {i}**" + (f" · _{cat}_" if cat else ""))
            st.markdown(turn.get("question", ""))
        with st.chat_message("user"):
            st.markdown(turn.get("answer", ""))

    # Pertanyaan yang sedang berjalan
    current = st.session_state.iv_current_q
    with st.chat_message("assistant"):
        cat = current.get("category", "")
        st.markdown(f"**Pertanyaan {q_no}**" + (f" · _{cat}_" if cat else ""))
        st.markdown(current.get("question", ""))

    # Input jawaban
    answer = st.text_area(
        "Jawaban kamu",
        key=f"iv_answer_{q_no}",
        placeholder="Ketik jawabanmu di sini...",
        height=140,
    )

    col_send, col_end = st.columns([1, 1])
    send_clicked = col_send.button("➡️ Kirim Jawaban", use_container_width=True, type="primary")
    end_clicked  = col_end.button("🏁 Selesai & Nilai Sekarang", use_container_width=True)

    if send_clicked:
        if not answer.strip():
            st.warning("Tulis jawaban dulu sebelum mengirim.")
            st.stop()

        # Catat giliran ini ke riwayat
        st.session_state.iv_history.append({
            "question": current.get("question", ""),
            "answer":   answer.strip(),
            "category": current.get("category", ""),
        })

        # Minta pertanyaan berikutnya / keputusan selesai dari agen
        with st.spinner("AI menyusun pertanyaan berikutnya..."):
            result = call_n8n(
                payload={
                    "mode":       "interview",
                    "action":     "answer",
                    "job_id":     job.get("job_id"),
                    "cv_profile": st.session_state.iv_cv_profile,
                    "history":    st.session_state.iv_history,
                },
                timeout=TIMEOUT_CHAT,
            )
        if "error" in result:
            show_error(result["error"])
            st.stop()

        if result.get("done"):
            # Agen menganggap wawancara cukup → langsung menilai
            apply_progress(result.get("progress", 100), done=True)
            run_assessment()
        else:
            st.session_state.iv_current_q = {
                "question":        result.get("question", ""),
                "category":        result.get("category", ""),
                "question_number": result.get("question_number", q_no + 1),
            }
            apply_progress(result.get("progress", 0), done=False)
            st.rerun()

    if end_clicked:
        # Akhiri lebih awal: jawaban saat ini disertakan bila ada isi
        if answer.strip():
            st.session_state.iv_history.append({
                "question": current.get("question", ""),
                "answer":   answer.strip(),
                "category": current.get("category", ""),
            })
        if not st.session_state.iv_history:
            st.warning("Jawab minimal satu pertanyaan sebelum meminta penilaian.")
            st.stop()
        run_assessment()


# ════════════════════════════════════════════════════════════════
# FASE 3 — DONE (FR-6.04, FR-6.05)
# ════════════════════════════════════════════════════════════════
elif st.session_state.iv_stage == "done":

    job = st.session_state.iv_job
    assessment = st.session_state.iv_assessment

    st.caption(
        f"🎯 Hasil wawancara untuk **{job.get('job_title', '-')}** "
        f"di {job.get('company_name', '-')}"
    )

    # ── Verdict (FR-6.04) ────────────────────────────────────────
    verdict = str(assessment.get("verdict", "-"))
    score = assessment.get("score", None)
    is_pass = verdict.strip().lower().startswith("bisa")
    accent = "#16A34A" if is_pass else "#DC2626"
    icon = "✅" if is_pass else "❌"
    score_html = (
        f'<div style="font-size:2rem;font-weight:800;color:{accent}">{score}<span '
        f'style="font-size:1rem;color:#64748B">/100</span></div>'
        if score is not None else ""
    )
    st.markdown(
        f'<div class="job-card" style="border-left:6px solid {accent}">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<h3 style="margin:0">{icon} {verdict}</h3>{score_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Alasan / kelebihan / perbaikan ───────────────────────────
    reasons = assessment.get("reasons", []) or []
    if reasons:
        section_lbl("Alasan Penilaian", "💡")
        for r in reasons:
            st.markdown(f"- {r}")

    col_s, col_i = st.columns(2)
    strengths = assessment.get("strengths", []) or []
    improvements = assessment.get("improvements", []) or []
    with col_s:
        if strengths:
            section_lbl("Kelebihan", "✅")
            for s in strengths:
                st.markdown(f'<span class="chip has">✓ {s}</span>', unsafe_allow_html=True)
    with col_i:
        if improvements:
            section_lbl("Perlu Ditingkatkan", "🎯")
            for m in improvements:
                st.markdown(f'<span class="chip miss">→ {m}</span>', unsafe_allow_html=True)

    # ── Transkrip + catatan per pertanyaan ───────────────────────
    per_q = assessment.get("per_question", []) or []
    with st.expander("📋 Lihat transkrip lengkap & catatan per pertanyaan"):
        for i, turn in enumerate(st.session_state.iv_history):
            cat = turn.get("category", "")
            st.markdown(f"**Q{i + 1}**" + (f" · _{cat}_" if cat else "") + f": {turn.get('question', '')}")
            st.markdown(f"> {turn.get('answer', '')}")
            if i < len(per_q):
                fb = per_q[i]
                fb_score = fb.get("score")
                score_txt = f" (nilai {fb_score}/10)" if fb_score is not None else ""
                if fb.get("feedback"):
                    st.caption(f"Catatan{score_txt}: {fb['feedback']}")
            st.markdown("")

    # ── Download PDF (FR-6.05) ───────────────────────────────────
    st.divider()
    pdf_bytes = build_interview_pdf(
        job=job,
        cv_profile=st.session_state.iv_cv_profile,
        history=st.session_state.iv_history,
        assessment=assessment,
    )
    col_dl, col_again = st.columns([1, 1])
    with col_dl:
        if pdf_bytes:
            st.download_button(
                "⬇️ Download Hasil (PDF)",
                data=pdf_bytes,
                file_name=f"wawancara_{job.get('job_title', 'lowongan')}.pdf".replace(" ", "_"),
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            # Fallback teks bila fpdf2 belum terinstall
            lines = [
                "TRANSKRIP SIMULASI WAWANCARA",
                f"Posisi: {job.get('job_title', '-')} | {job.get('company_name', '-')}",
                f"Verdict: {verdict} (Skor: {score}/100)",
                "",
            ]
            for i, turn in enumerate(st.session_state.iv_history, start=1):
                lines.append(f"Q{i}: {turn.get('question', '')}")
                lines.append(f"Jawaban: {turn.get('answer', '')}")
                lines.append("")
            st.download_button(
                "⬇️ Download Hasil (teks)",
                data="\n".join(lines).encode("utf-8"),
                file_name=f"wawancara_{job.get('job_title', 'lowongan')}.txt".replace(" ", "_"),
                mime="text/plain",
                use_container_width=True,
            )
            st.caption("PDF tidak tersedia (fpdf2 belum terinstall). Jalankan: pip install fpdf2")
    with col_again:
        if st.button("🔄 Ulangi Wawancara", use_container_width=True):
            reset_interview()
            st.rerun()
