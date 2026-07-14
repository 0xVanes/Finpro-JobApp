"""
Simulasi Wawancara (Interview Agent) — FR-6.01 s/d FR-6.05.

Arsitektur multi-agent (coordinator + sub-agent) di n8n:
- Planner  : menyusun 4-6 POIN INTI wawancara + pertanyaan pertama.
- Monitor  : menilai apakah poin saat ini sudah cukup terjawab.
- Questioner: memberi tanggapan manusiawi lalu pertanyaan berikutnya.
- Assessor : verdict akhir.

Panjang sesi & progress ditentukan STRUKTUR poin, bukan tebakan agen:
progress = (poin_saat_ini - 1) / total_poin. Deterministik & monotonik.

Kontrak webhook & alur lengkap: lihat docs/interview.md.
"""

import html

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
    "iv_plan":           [],         # [{index, point, category}] dari Planner
    "iv_total_points":   0,          # K poin inti
    "iv_current_point_index": 1,     # poin yang sedang dibahas (1-based)
    "iv_point_qcount":   1,          # jumlah pertanyaan pada poin saat ini
    "iv_history":        [],         # [{question, answer, category, point_index, reaction}]
    "iv_current_q":      {},         # {reaction, question, category} yang menunggu jawaban
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


def running_progress() -> int:
    """
    Progress deterministik dari struktur poin (bukan tebakan agen):
    (poin_saat_ini - 1) / total_poin. Selalu monotonik karena indeks poin
    hanya bertambah; mencapai 100% hanya setelah poin terakhir tuntas (done).
    """
    total = st.session_state.iv_total_points or 1
    idx = st.session_state.iv_current_point_index or 1
    return max(0, min(round((idx - 1) / total * 100), 99))


def run_assessment(history: list) -> None:
    """
    Panggil action=assess. Riwayat baru di-commit ke session_state HANYA bila
    backend menjawab — supaya percobaan ulang setelah gagal tidak menggandakan
    entri (lihat catatan atomic commit di kirim jawaban).
    """
    with st.spinner("AI menilai keseluruhan wawancara..."):
        result = call_n8n(
            payload={
                "mode":         "interview",
                "action":       "assess",
                "job_id":       st.session_state.iv_job.get("job_id"),
                "cv_profile":   st.session_state.iv_cv_profile,
                "plan":         st.session_state.iv_plan,
                "history":      history,
            },
            timeout=TIMEOUT_CV,
        )
    if "error" in result:
        show_error(result["error"])
        return
    st.session_state.iv_history = history
    st.session_state.iv_assessment = result
    st.session_state.iv_stage = "done"
    st.rerun()


def italic(text: object) -> str:
    """
    Render teks miring lewat HTML, bukan markdown `_..._`.

    Markdown tersandung underscore di dalam kata (mis. kategori "soft_skill")
    sehingga garis bawahnya bocor sebagai karakter literal. HTML + escape
    membuat teks apa pun aman ditampilkan.
    """
    return (
        f'<span style="font-style:italic;color:#64748B">'
        f'{html.escape(str(text))}</span>'
    )


def as_point(item: object) -> tuple[str, str]:
    """
    Normalisasi butir penilaian menjadi (teks, bukti).

    Assessor kini mengembalikan objek `{point, evidence}`; bentuk string lama
    tetap didukung agar respons versi sebelumnya tidak merusak tampilan.
    """
    if isinstance(item, dict):
        return str(item.get("point", "")), str(item.get("evidence", "") or "")
    return str(item), ""


def render_interviewer(turn: dict, heading: str = "") -> None:
    """Tampilkan giliran pewawancara: tanggapan (jika ada) lalu pertanyaan."""
    with st.chat_message("assistant"):
        if heading:
            st.markdown(heading)
        reaction = turn.get("reaction", "")
        if reaction:
            st.markdown(italic(reaction), unsafe_allow_html=True)
        st.markdown(turn.get("question", ""))


# ════════════════════════════════════════════════════════════════
# FASE 1 — SETUP (FR-6.01)
# ════════════════════════════════════════════════════════════════
if st.session_state.iv_stage == "setup":

    # ── Langkah 1: Upload CV ─────────────────────────────────────
    section_lbl("1. Upload CV kamu (FR-4.01)", "📄")
    uploaded = st.file_uploader(
        "CV (PDF atau DOCX) — tidak disimpan permanen (NFR-5.01)",
        type=["pdf", "docx"],
        help="Rencana & pertanyaan wawancara disusun dari isi CV ini dan lowongan yang dipilih.",
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

        # Panggil action=start → Planner menyusun rencana poin + pertanyaan pertama
        with st.spinner("AI menyusun rencana wawancara..."):
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

        plan = result.get("plan", []) or []
        if not plan:
            show_error("AI gagal menyusun rencana wawancara. Coba lagi.")
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
        st.session_state.iv_plan                = plan
        st.session_state.iv_total_points        = result.get("total_points", len(plan))
        st.session_state.iv_current_point_index = result.get("current_point_index", 1)
        st.session_state.iv_point_qcount        = 1
        st.session_state.iv_current_q = {
            "reaction": "",   # pertanyaan pertama tidak menanggapi jawaban apa pun
            "question": result.get("question", ""),
            "category": result.get("category", ""),
        }
        st.session_state.iv_history = []
        st.session_state.iv_stage = "running"
        st.rerun()


# ════════════════════════════════════════════════════════════════
# FASE 2 — RUNNING (FR-6.02, FR-6.03)
# ════════════════════════════════════════════════════════════════
elif st.session_state.iv_stage == "running":

    job = st.session_state.iv_job
    plan = st.session_state.iv_plan
    total = st.session_state.iv_total_points or len(plan)
    cur_idx = st.session_state.iv_current_point_index

    st.caption(
        f"🎯 Wawancara untuk **{job.get('job_title', '-')}** "
        f"di {job.get('company_name', '-')}"
    )

    # Progress bar deterministik dari poin
    pct = running_progress()
    st.progress(pct / 100, text=f"Progres: {pct}%  ·  Poin {cur_idx}/{total}")

    # Rencana poin inti (transparansi struktur wawancara)
    with st.expander("🗂️ Poin inti yang dinilai"):
        for pt in plan:
            i = pt.get("index", 0)
            mark = "✅" if i < cur_idx else ("🔹" if i == cur_idx else "⚪")
            st.markdown(
                f"{mark} **{i}.** {pt.get('point', '-')} · {italic(pt.get('category', ''))}",
                unsafe_allow_html=True,
            )

    # Riwayat Q&A yang sudah dijawab
    for turn in st.session_state.iv_history:
        render_interviewer(turn)
        with st.chat_message("user"):
            st.markdown(turn.get("answer", ""))

    # Semua poin tuntas tetapi penilaian belum tersimpan (mis. assess sempat gagal)
    current = st.session_state.iv_current_q
    if not current.get("question"):
        st.success("Semua poin inti sudah tuntas. Tinggal penilaian akhir.")
        if st.button("📊 Nilai Sekarang", use_container_width=True, type="primary"):
            run_assessment(st.session_state.iv_history)
        st.stop()

    # Pertanyaan yang sedang berjalan (tanggapan + pertanyaan)
    render_interviewer(current)

    # Input jawaban
    answer = st.text_area(
        "Jawaban kamu",
        key=f"iv_answer_{len(st.session_state.iv_history)}",
        placeholder="Ketik jawabanmu di sini...",
        height=140,
    )

    col_send, col_end = st.columns([1, 1])
    send_clicked = col_send.button("➡️ Kirim Jawaban", use_container_width=True, type="primary")
    end_clicked  = col_end.button("🏁 Selesai & Nilai Sekarang", use_container_width=True)

    def _pending_turn(text: str) -> dict:
        """Susun giliran saat ini TANPA menyentuh session_state (belum di-commit)."""
        return {
            "question":    current.get("question", ""),
            "answer":      text.strip(),
            "category":    current.get("category", ""),
            "point_index": st.session_state.iv_current_point_index,
            "reaction":    current.get("reaction", ""),
        }

    if send_clicked:
        if not answer.strip():
            st.warning("Tulis jawaban dulu sebelum mengirim.")
            st.stop()

        # ATOMIC COMMIT: riwayat baru disiapkan di variabel lokal dan dikirim ke n8n,
        # tetapi baru ditulis ke session_state SETELAH backend menjawab. Kalau koneksi
        # gagal, riwayat tetap utuh sehingga percobaan ulang tidak menggandakan entri.
        history_next = st.session_state.iv_history + [_pending_turn(answer)]

        # Monitor menilai poin → Decide (cap 5) → Questioner (tanggapan + pertanyaan)
        with st.spinner("Pewawancara menanggapi jawabanmu..."):
            result = call_n8n(
                payload={
                    "mode":                "interview",
                    "action":              "answer",
                    "job_id":              job.get("job_id"),
                    "cv_profile":          st.session_state.iv_cv_profile,
                    "plan":                st.session_state.iv_plan,
                    "total_points":        st.session_state.iv_total_points,
                    "current_point_index": st.session_state.iv_current_point_index,
                    "point_qcount":        st.session_state.iv_point_qcount,
                    "history":             history_next,
                },
                timeout=TIMEOUT_CHAT,
            )
        if "error" in result:
            show_error(result["error"] + "  Jawabanmu belum terkirim — silakan coba lagi.")
            st.stop()

        # Backend menerima → baru commit
        st.session_state.iv_history = history_next
        st.session_state.iv_current_point_index = result.get(
            "current_point_index", st.session_state.iv_current_point_index)
        st.session_state.iv_point_qcount = result.get(
            "point_qcount", st.session_state.iv_point_qcount)

        if result.get("done"):
            # Semua poin tuntas → kosongkan pertanyaan berjalan lalu nilai
            st.session_state.iv_current_q = {}
            run_assessment(st.session_state.iv_history)
            st.rerun()          # assess gagal → tampilkan tombol "Nilai Sekarang"
        else:
            st.session_state.iv_current_q = {
                "reaction": result.get("reaction", ""),
                "question": result.get("question", ""),
                "category": result.get("category", ""),
            }
            st.rerun()

    if end_clicked:
        history_next = st.session_state.iv_history + (
            [_pending_turn(answer)] if answer.strip() else []
        )
        if not history_next:
            st.warning("Jawab minimal satu pertanyaan sebelum meminta penilaian.")
            st.stop()
        run_assessment(history_next)   # commit terjadi di dalam, hanya bila sukses


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
    st.caption(
        "Skor dihitung sistem sebagai rata-rata rubrik di bawah — bukan angka tunggal "
        "dari AI. Verdict mengikuti ambang 70/100."
    )

    # ── Cakupan wawancara & tingkat keyakinan ────────────────────
    coverage = assessment.get("coverage", {}) or {}
    confidence = str(assessment.get("confidence", "") or "")
    if coverage or confidence:
        conf_color = {"high": "#16A34A", "medium": "#D97706", "low": "#DC2626"}.get(
            confidence, "#64748B")
        conf_text = {"high": "Tinggi", "medium": "Sedang", "low": "Rendah"}.get(
            confidence, confidence or "—")
        c1, c2 = st.columns([1, 2])
        c1.metric(
            "Cakupan wawancara",
            f"{coverage.get('ratio_pct', 0)}%",
            help="Berapa persen poin inti yang benar-benar tergali.",
        )
        with c2:
            st.markdown(
                f'<div style="margin-top:.6rem">Keyakinan penilaian: '
                f'<b style="color:{conf_color}">{conf_text}</b> · '
                f'{coverage.get("explored_count", 0)}/{coverage.get("total_points", 0)} '
                f'poin tergali</div>',
                unsafe_allow_html=True,
            )
            if coverage.get("note"):
                st.caption(coverage["note"])

        # Skill di CV/lowongan yang tak pernah ditanyakan sama sekali.
        # Ditampilkan terpisah agar cakupan tidak terbaca "lengkap" hanya karena
        # semua poin buatan Planner tergali (penilaian sirkular).
        untested = coverage.get("untested_areas", []) or []
        if untested:
            st.markdown(
                "".join(f'<span class="chip miss">⚠ {u}</span>' for u in untested),
                unsafe_allow_html=True,
            )
            st.caption(
                "Area di CV/lowongan yang **tidak pernah diuji** dalam sesi ini — "
                "menurunkan tingkat keyakinan penilaian."
            )

    # ── Rubrik per dimensi ───────────────────────────────────────
    DIM_LABEL = {
        "technical_depth":   "Kedalaman Teknis",
        "problem_framing":   "Perumusan Masalah",
        "communication":     "Komunikasi",
        "rigor_and_honesty": "Kecermatan & Kejujuran",
        "impact":            "Dampak",
    }
    dimensions = assessment.get("dimensions", []) or []
    if dimensions:
        section_lbl("Rubrik Penilaian (dasar skor)", "📊")
        for dim in dimensions:
            name = DIM_LABEL.get(dim.get("name", ""), dim.get("name", "—"))
            dscore = dim.get("score")
            try:
                frac = max(0.0, min(float(dscore) / 10, 1.0))
            except (TypeError, ValueError):
                frac = 0.0
            st.progress(frac, text=f"{name} — {dscore}/10")
            if dim.get("evidence"):
                st.caption(f"Bukti: {dim['evidence']}")

    # ── Alasan ───────────────────────────────────────────────────
    reasons = assessment.get("reasons", []) or []
    if reasons:
        section_lbl("Alasan Penilaian", "💡")
        for r in reasons:
            st.markdown(f"- {r}")

    # ── Kelebihan / perlu ditingkatkan (dengan bukti) ────────────
    col_s, col_i = st.columns(2)
    with col_s:
        strengths = assessment.get("strengths", []) or []
        if strengths:
            section_lbl("Kelebihan", "✅")
            for item in strengths:
                point, evidence = as_point(item)
                st.markdown(f'<span class="chip has">✓ {point}</span>',
                            unsafe_allow_html=True)
                if evidence:
                    st.caption(f"Bukti: {evidence}")
    with col_i:
        improvements = assessment.get("improvements", []) or []
        if improvements:
            section_lbl("Perlu Ditingkatkan", "🎯")
            for item in improvements:
                point, evidence = as_point(item)
                kind = item.get("type", "") if isinstance(item, dict) else ""
                tag = " (belum diuji)" if kind == "not_tested" else ""
                st.markdown(f'<span class="chip miss">→ {point}{tag}</span>',
                            unsafe_allow_html=True)
                if evidence:
                    st.caption(f"Bukti: {evidence}")

    # ── Kesadaran diri: kejujuran dikreditkan, bukan dihukum ─────
    self_awareness = assessment.get("self_awareness", []) or []
    if self_awareness:
        section_lbl("Kesadaran Diri (dinilai positif)", "🪞")
        st.caption(
            "Keterbatasan yang diakui sendiri oleh kandidat dicatat sebagai sinyal "
            "kematangan, bukan kelemahan."
        )
        for item in self_awareness:
            point, evidence = as_point(item)
            st.markdown(f'<span class="chip has">🪞 {point}</span>', unsafe_allow_html=True)
            if evidence:
                st.caption(f"Bukti: {evidence}")

    # ── Transkrip + catatan per pertanyaan ───────────────────────
    per_q = assessment.get("per_question", []) or []
    with st.expander("📋 Lihat transkrip lengkap & catatan per pertanyaan"):
        for i, turn in enumerate(st.session_state.iv_history):
            cat = turn.get("category", "")
            if turn.get("reaction"):
                st.markdown(italic(turn["reaction"]), unsafe_allow_html=True)
            st.markdown(
                f"**Q{i + 1}**" + (f" · {italic(cat)}" if cat else "")
                + f": {turn.get('question', '')}",
                unsafe_allow_html=True,
            )
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
