"""
utils.py — Shared utilities JobPath
=====================================
Berisi konfigurasi, CSS, dan helper functions yang dipakai
bersama oleh seluruh halaman di pages/.

Prinsip kode yang diterapkan:
    - Type hints pada semua fungsi publik  (PEP 484)
    - Docstring pada semua fungsi          (PEP 257)
    - Konstanta kapital untuk magic values (PEP 8)
    - Error handling eksplisit, tidak bare-except
    - Tidak ada HTML inline di luar fungsi render
    - Import di level modul, bukan di dalam fungsi

Cara pakai di setiap page:
    from utils import setup_page, call_n8n, hero, job_card, show_error
"""

from __future__ import annotations

import io
import logging
from typing import Optional
import os
import requests
import streamlit as st

# ─── KONSTANTA KONFIGURASI (NFR-4.03) ───────────────────────────
# Semua nilai sensitif dari st.secrets / environment variable
# Tidak ada credential yang di-hardcode di sini
# Muat .env secara eksplisit di sini agar N8N_WEBHOOK_URL tersedia tanpa
# bergantung pada urutan import halaman. find_dotenv() menelusuri ke atas
# dari cwd untuk menemukan .env di root repo.
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(), override=True)
N8N_WEBHOOK_URL: str = os.environ.get("N8N_WEBHOOK_URL")
# Satu logger per modul — tidak pakai print() untuk error internal
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Timeout (detik) per jenis request sesuai NFR-2
TIMEOUT_CHAT:  int = 15   # NFR-2.01 RAG chat ≤ 15 s
TIMEOUT_SQL:   int = 40   # SQL Search Agent (LLM + MySQL tool) butuh ~34s
TIMEOUT_CV:    int = 80   # NFR-2.03 CV extract ≤ 30 s
TIMEOUT_OTHER: int = 20   # Default untuk mode lainnya

# Format file CV yang didukung (NFR-3.02)
SUPPORTED_CV_TYPES: tuple[str, ...] = ("pdf", "docx")


# ─── HELPER: N8N ────────────────────────────────────────────────

def call_n8n(payload: dict, timeout: int = TIMEOUT_OTHER) -> dict:
    """
    Kirim request ke N8N webhook dan kembalikan respons JSON.

    Semua exception ditangkap dan dikembalikan sebagai
    ``{"error": pesan}`` sehingga caller tinggal cek key "error".
    Tidak ada traceback Python yang bocor ke UI (NFR-3.02).

    Args:
        payload: Dict yang akan di-serialize menjadi JSON body.
        timeout: Batas waktu tunggu dalam detik.

    Returns:
        Dict hasil JSON dari N8N, atau ``{"error": str}`` jika gagal.
    """
    try:
        response = requests.post(N8N_WEBHOOK_URL,json=payload,timeout=timeout,)
        response.raise_for_status()
        return response.json()                          # type: ignore[no-any-return]

    except requests.exceptions.Timeout:
        logger.warning("N8N timeout setelah %ds — payload mode: %s",
                       timeout, payload.get("mode", "?"))
        return {"error": (
            f"""⏱️ Waktu habis ({timeout}s).
            Server sedang sibuk, silakan coba lagi.""" + N8N_WEBHOOK_URL)}

    except requests.exceptions.ConnectionError:
        logger.error("Tidak dapat menjangkau N8N: %s", N8N_WEBHOOK_URL)
        return {"error": (
            "🔌 Tidak dapat terhubung ke layanan AI. "
            "Periksa koneksi internet kamu."
        )}

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        logger.error("N8N HTTP error %s — payload: %s", status, payload)
        return {"error": f"🚫 Server merespons dengan kode {status}. Coba lagi."}

    except ValueError as exc:
        # JSON decode error
        logger.error("N8N respons bukan JSON valid: %s", exc)
        return {"error": "⚠️ Respons dari server tidak dapat dibaca. Hubungi administrator."}

    except Exception as exc:                            # noqa: BLE001
        logger.exception("N8N call gagal tidak terduga: %s", exc)
        return {"error": "❌ Terjadi kesalahan tak terduga. Hubungi administrator."}


# ─── HELPER: CV ─────────────────────────────────────────────────

def extract_cv_text(uploaded_file) -> str:
    """
    Ekstrak teks mentah dari file CV yang diupload.

    Mendukung PDF dan DOCX. File hanya dibaca ke memory (NFR-5.01),
    tidak disimpan ke disk. Timeout dikontrol di sisi caller via
    TIMEOUT_CV saat memanggil call_n8n() setelahnya.

    Args:
        uploaded_file: Objek UploadedFile dari st.file_uploader().

    Returns:
        String teks hasil ekstraksi, atau string kosong jika gagal.

    Raises:
        Tidak raise — semua exception di-catch dan di-log.
    """
    try:
        raw_bytes = uploaded_file.getvalue()
        file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if file_ext == "pdf":
            return _extract_pdf(raw_bytes)
        elif file_ext == "docx":
            return _extract_docx(raw_bytes)
        else:
            logger.warning("Format CV tidak didukung: .%s", file_ext)
            return ""

    except Exception as exc:                            # noqa: BLE001
        logger.error("extract_cv_text gagal: %s", exc)
        return ""

## ganti bytesio(binary n8n)
def _extract_pdf(raw: bytes) -> str:
    """Ekstrak teks dari bytes PDF menggunakan pypdf."""
    try:
        from pypdf import PdfReader          # lazy import — opsional dependency
        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except ImportError:
        logger.error("pypdf tidak terinstall. Jalankan: pip install pypdf")
        return ""
    except Exception as exc:
        logger.error("Gagal membaca PDF: %s", exc)
        return ""


def _extract_docx(raw: bytes) -> str:
    """Ekstrak teks dari bytes DOCX menggunakan python-docx."""
    try:
        from docx import Document           # lazy import — opsional dependency
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        logger.error("python-docx tidak terinstall. Jalankan: pip install python-docx")
        return ""
    except Exception as exc:
        logger.error("Gagal membaca DOCX: %s", exc)
        return ""


def validate_cv_upload(uploaded_file) -> tuple[bool, str]:
    """
    Validasi file CV sebelum diproses.

    Args:
        uploaded_file: Objek UploadedFile dari st.file_uploader().

    Returns:
        Tuple (valid: bool, pesan_error: str).
        Jika valid, pesan_error adalah string kosong.
    """
    if uploaded_file is None:
        return False, "Belum ada file yang diupload."

    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    if ext not in SUPPORTED_CV_TYPES:
        return False, (
            f"Format '{ext}' tidak didukung. "
            f"Harap upload file PDF atau DOCX."
        )

    # Batas ukuran 10 MB
    max_bytes = 10 * 1024 * 1024
    if uploaded_file.size > max_bytes:
        return False, (
            f"File terlalu besar ({uploaded_file.size // 1024 // 1024} MB). "
            "Maksimal 10 MB."
        )

    return True, ""


# ─── HELPER: RENDER KOMPONEN UI ─────────────────────────────────

def section_lbl(text: str, icon: str = "") -> None:
    """
    Render label bagian kecil berwarna sebelum kelompok konten.

    Args:
        text: Teks label (akan ditampilkan uppercase).
        icon: Emoji opsional di depan teks.
    """
    prefix = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="section-lbl">{prefix}{text}</div>',
        unsafe_allow_html=True,
    )

def render_skill_chips(matching: list[str], missing: list[str]) -> None:
    """
    Render chip skill dengan warna berbeda: hijau (cocok) vs oranye (kurang).

    Args:
        matching: Skill yang sudah dimiliki kandidat.
        missing:  Skill yang perlu dikembangkan.
    """
    chips = (
        "".join(f'<span class="chip has">✓ {s}</span>' for s in matching)
        + "".join(f'<span class="chip miss">✗ {s}</span>' for s in missing)
    )
    if chips:
        st.markdown(chips, unsafe_allow_html=True)


def show_error(message: str) -> None:
    """
    Tampilkan kotak error ramah pengguna tanpa traceback Python (NFR-3.02).

    Args:
        message: Pesan error yang akan ditampilkan ke pengguna.
    """
    st.markdown(
        f'<div class="err-box">{message}</div>',
        unsafe_allow_html=True,
    )

def job_card(job: dict) -> None:
    """
    Render kartu lowongan dengan format seragam.

    Menggunakan .get() dengan default di semua field
    sehingga tidak crash jika field tidak ada di respons N8N.

    Args:
        job: Dict berisi data lowongan dari N8N.
    """
    salary = job.get("salary") or job.get("salary_raw") or "Tidak disebutkan"
    if salary in ("None", "null", ""):
        salary = "Tidak disebutkan"

    reason = job.get("relevance_reason") or job.get("reason") or ""
    rank   = job.get("rank", "")

    rank_html   = (
        f'<div style="font-size:.7rem;color:#6D5DF6;font-weight:700;'
        f'margin-bottom:2px">{rank}</div>'
    ) if rank else ""

    reason_html = (
        f'<div class="reason">💡 {reason}</div>'
    ) if reason else ""

    st.markdown(
        f'<div class="jp-card">'
        f'{rank_html}'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'<div class="card-icon" style="width:36px;height:36px;border-radius:10px;'
        f'background:linear-gradient(135deg,#6D5DF6,#00C2A8);'
        f'display:flex;align-items:center;justify-content:center;'
        f'flex-shrink:0;color:#fff;font-size:18px">💼</div>'
        f'<h3>{job.get("job_title", "N/A")}</h3>'
        f'</div>'
        f'<div class="company" style="margin-top:4px">'
        f'{job.get("company_name", "N/A")}</div>'
        f'<div class="meta">'
        f'📍 {job.get("location", "N/A")} · {job.get("work_type", "N/A")}</div>'
        f'<div style="margin-top:8px">'
        f'<span class="sal-tag">💰 {salary}</span></div>'
        f'{reason_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

def job_card(job: dict) -> None:
    """
    Render kartu lowongan dengan format seragam.

    Menggunakan .get() dengan default di semua field
    sehingga tidak crash jika field tidak ada di respons N8N.

    Args:
        job: Dict berisi data lowongan dari N8N.
    """
    salary = job.get("salary") or job.get("salary_raw") or "Tidak disebutkan"
    if salary in ("None", "null", ""):
        salary = "Tidak disebutkan"

    reason = job.get("relevance_reason") or job.get("reason") or ""
    rank   = job.get("rank", "")

    rank_html   = (
        f'<div style="font-size:.7rem;color:#6D5DF6;font-weight:700;'
        f'margin-bottom:2px">{rank}</div>'
    ) if rank else ""

    reason_html = (
        f'<div class="reason">💡 {reason}</div>'
    ) if reason else ""

    st.markdown(
        f'<div class="jp-card">'
        f'{rank_html}'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'<div class="card-icon" style="width:36px;height:36px;border-radius:10px;'
        f'background:linear-gradient(135deg,#6D5DF6,#00C2A8);'
        f'display:flex;align-items:center;justify-content:center;'
        f'flex-shrink:0;color:#fff;font-size:18px">💼</div>'
        f'<h3>{job.get("job_title", "N/A")}</h3>'
        f'</div>'
        f'<div class="company" style="margin-top:4px">'
        f'{job.get("company_name", "N/A")}</div>'
        f'<div class="meta">'
        f'📍 {job.get("location", "N/A")} · {job.get("work_type", "N/A")}</div>'
        f'<div style="margin-top:8px">'
        f'<span class="sal-tag">💰 {salary}</span></div>'
        f'{reason_html}'
        f'</div>',
        unsafe_allow_html=True,
    )