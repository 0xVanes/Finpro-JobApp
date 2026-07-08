# Simulasi Wawancara — Interview Agent (JobPath)

Dokumentasi fitur **Simulasi Wawancara** (`FR-6.01`–`FR-6.05`). Menetapkan kontrak
antara halaman Streamlit `pages/6interview.py` dan workflow n8n, sehingga kedua sisi
dapat dikembangkan terpisah selama patuh pada kontrak ini.

## Prinsip desain

Wawancara bersifat **percakapan bergiliran** (tanya → jawab → tanya lagi → penilaian),
berbeda dari fitur lain yang satu-request-satu-response. Webhook n8n tetap **stateless**
(`NFR-1.02`): setiap panggilan adalah HTTP request independen. Karena itu:

> **State percakapan hidup di `st.session_state` (Streamlit).** Setiap request ke n8n
> membawa seluruh riwayat Q&A sejauh ini. n8n tidak menyimpan state — ia menerima
> "profil CV + lowongan + riwayat" lalu menghasilkan pertanyaan atau penilaian berikutnya.

Fitur ini terikat pada **lowongan nyata** di database (`FR-6.01`): pertanyaan disusun
berdasarkan `job_description` lowongan yang dipilih **dan** CV pengguna. **Panjang sesi
ditentukan agen** (bukan jumlah tetap) — agen memutuskan kapan wawancara cukup.

## Alur (state machine 3 fase)

```
FASE 1 — SETUP
  1. Upload CV (reuse extract_cv_text di utils.py — FR-4.01, NFR-5.01)
  2. Ketik kata kunci → pilih 1 lowongan nyata dari hasil pencarian (FR-6.01)
  [Mulai] → call_n8n(action="start", cv_text, job_id)

FASE 2 — RUNNING (agen mengontrol panjang sesi)
  Tampilkan pertanyaan → pengguna menjawab teks (FR-6.03)
  Submit → history.append({question, answer, category})
  call_n8n(action="answer", cv_profile, job_id, history)
    - response { done:false, question:... } → tampilkan pertanyaan berikutnya (FR-6.02)
    - response { done:true }                → agen menganggap cukup → lanjut assess

FASE 3 — DONE
  call_n8n(action="assess", cv_profile, job_id, history)
  Tampilkan verdict "Bisa Diterima / Tidak" + alasan (FR-6.04)
  Tombol Download PDF: transkrip + penilaian (FR-6.05)
```

## Kontrak webhook

Semua request memakai webhook yang sama (`job-assistant`) dengan `mode: "interview"`,
dibedakan oleh field `action`. Konsisten dengan `mode` chat / search / cv_match yang
sudah ada; cukup menambah satu cabang pada node Switch "Route by Mode" di n8n.

### 0. Pemilihan lowongan — `mode: "search"` (reuse)

Setup memakai ulang pencarian yang sudah ada untuk menampilkan lowongan nyata.

**Syarat kontrak:** setiap item pada `jobs` **wajib** menyertakan `job_id`. Tanpa ini,
halaman interview tidak dapat mengambil `job_description` lowongan terpilih.

```json
// request
{ "mode": "search", "keyword": "Data Analyst", "work_type": null,
  "city": null, "salary_min": null, "hybrid_only": false }

// response — job_id WAJIB ada di tiap item
{ "jobs": [
    { "job_id": "0052b191-...", "job_title": "Data Analyst",
      "company_name": "PT Vita Shopindo", "location": "Jakarta Barat",
      "work_type": "Full-time" }
  ],
  "top_cities": [ ... ] }
```

### 1. `action: "start"` — mulai wawancara

Agen membaca CV penuh + `job_description` (ditarik dari `job_id`), lalu mengeluarkan
pertanyaan pertama. Response mengembalikan `cv_profile` ringkas agar request berikutnya
tidak perlu mengirim ulang `cv_text` penuh.

```json
// request
{ "mode": "interview", "action": "start",
  "cv_text": "<teks CV hasil ekstraksi>",
  "job_id": "0052b191-...", "position": "Data Analyst" }

// response
{ "cv_profile": { "current_role": "Junior Analyst", "experience_years": 1,
                  "key_skills": ["SQL", "Excel", "Python"] },
  "question": "Ceritakan proyek analisis data yang pernah kamu kerjakan.",
  "category": "technical", "question_number": 1,
  "progress": 10, "done": false }
```

### 2. `action: "answer"` — kirim jawaban, minta giliran berikutnya

Streamlit mengirim seluruh riwayat Q&A. Agen memutuskan menampilkan pertanyaan
berikutnya atau mengakhiri wawancara (`done: true`).

```json
// request
{ "mode": "interview", "action": "answer",
  "job_id": "0052b191-...",
  "cv_profile": { ... },              // dari response start
  "history": [
    { "question": "...", "answer": "...", "category": "technical" }
  ] }

// response — lanjut
{ "done": false,
  "question": "Bagaimana kamu menangani data yang tidak lengkap?",
  "category": "technical", "question_number": 2, "progress": 45 }

// response — selesai
{ "done": true, "progress": 100 }
```

### 3. `action: "assess"` — penilaian akhir (FR-6.04)

Dipanggil setelah agen mengirim `done: true`. Agen menilai transkrip penuh terhadap
CV dan lowongan.

```json
// request
{ "mode": "interview", "action": "assess",
  "job_id": "0052b191-...", "cv_profile": { ... },
  "history": [ { "question": "...", "answer": "...", "category": "..." }, ... ] }

// response
{ "verdict": "Bisa Diterima",          // "Bisa Diterima" | "Tidak"
  "score": 78,                          // 0-100
  "reasons": [ "Menguasai SQL sesuai kebutuhan lowongan", "..." ],
  "strengths": [ "Komunikasi jelas", "..." ],
  "improvements": [ "Perdalam statistik", "..." ],
  "per_question": [
    { "question": "...", "feedback": "...", "score": 8 }   // score 0-10
  ] }
```

## Progress bar

Karena panjang sesi tidak tetap, persentase progres berasal dari **agen** (field
`progress`, 0–100) pada response `start` / `answer`. Streamlit menampilkannya dengan
aturan berikut agar tidak menyesatkan:

- **Monotonik** — tidak pernah mundur: `tampil = max(tampil_lama, progress_agen)`.
- **Tidak pernah 100% sebelum `done`** — dibatasi maksimal `95` selama berjalan.
- **Snap ke 100%** begitu `done: true`.

Ringkas: `tampil = min( max(tampil_lama, progress_agen), 95 )` saat berjalan; `100` saat done.

## Arsitektur agen di n8n (NFR-1.01 multi-agent)

Dua agent di dalam cabang `mode == interview`:

1. **Interviewer Agent** — input: `cv_profile` + `job_description` (dari `job_id`) +
   `history`. Output: satu pertanyaan berikutnya **atau** keputusan `done: true`.
   Menyertakan `progress` (naik bertahap; mendekati 100 hanya saat akan mengakhiri).
   Campuran pertanyaan teknis dan HR, menyesuaikan jawaban sebelumnya.

2. **Assessor Agent** — input: transkrip penuh + `cv_profile` + `job_description`.
   Output: verdict + skor + alasan + catatan per pertanyaan.

Kontrak output kedua agent harus JSON valid. Terapkan parsing toleran seperti pada node
*Format Search Response* (ekstrak blok `{...}` bila `JSON.parse` langsung gagal) untuk
menghindari kegagalan format saat LLM menambah teks di luar JSON.

## State di Streamlit (`st.session_state`)

| Key | Tipe | Guna |
|---|---|---|
| `iv_stage` | str | `"setup"` / `"running"` / `"done"` |
| `iv_cv_text` | str | teks CV hasil ekstraksi (dikirim di `start`) |
| `iv_cv_profile` | dict | profil ringkas dari response `start` |
| `iv_job` | dict | lowongan terpilih: `job_id`, `job_title`, `company_name` |
| `iv_history` | list | `[{question, answer, category}]` |
| `iv_current_q` | dict | pertanyaan yang sedang menunggu jawaban |
| `iv_progress` | int | nilai progress tampil (setelah clamp) |
| `iv_assessment` | dict | hasil verdict akhir |

## Penanganan error (NFR-3.02)

Semua panggilan lewat `call_n8n()` sehingga timeout, koneksi putus, HTTP error, dan JSON
tak valid sudah dikembalikan sebagai `{"error": <pesan ramah>}` tanpa traceback. Halaman
menampilkannya via `show_error()`. Timeout memakai `TIMEOUT_CHAT` (giliran tanya-jawab
berbasis satu agent) dan `TIMEOUT_CV` untuk `assess` bila penilaian lebih berat.

## Privasi (NFR-5.01)

CV hanya diproses di memory selama sesi. `cv_text` dikirim sekali di `start`; giliran
berikutnya cukup membawa `cv_profile` ringkas. Tidak ada penyimpanan CV permanen.
