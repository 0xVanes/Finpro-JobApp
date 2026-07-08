# Simulasi Wawancara — Interview Agent (JobPath)

Dokumentasi fitur **Simulasi Wawancara** (`FR-6.01`–`FR-6.05`). Menetapkan kontrak
antara halaman Streamlit `pages/6interview.py` dan sub-workflow n8n `6-interview.json`.

## Prinsip desain

Wawancara adalah **percakapan bergiliran** (tanya → jawab → tanggapi → tanya lagi →
penilaian). Webhook n8n **stateless** (`NFR-1.02`): setiap panggilan independen. Karena itu:

> **State percakapan hidup di `st.session_state` (Streamlit).** Setiap request membawa
> seluruh riwayat + rencana wawancara. n8n tidak menyimpan state.

Fitur terikat pada **lowongan nyata** (`FR-6.01`): pertanyaan disusun dari `job_description`
lowongan terpilih **dan** CV pengguna.

**Panjang sesi & progress ditentukan STRUKTUR, bukan tebakan agen.** Di awal, *Planner*
menyusun **K poin inti** (4–6). Progress dihitung deterministik:

```
progress = 100                              jika semua poin tuntas (done)
         = (current_point_index − 1) / K × 100   selain itu
```

Indeks poin hanya bertambah → progress **monotonik** dan pasti mencapai 100%. Ini
menggantikan pendekatan lama (agen menebak `progress`) yang menyebabkan bar mandek.

## Arsitektur multi-agent (NFR-1.01)

Koordinasi dipegang alur kerja + indeks di Streamlit (deterministik), dengan empat agen di
sub-workflow `6-interview.json`:

| Agen | Peran |
|---|---|
| **Planner** (`start`) | susun rencana K poin inti + profil CV + pertanyaan pertama |
| **Monitor** (`answer`) | nilai apakah poin saat ini sudah cukup terjawab (`point_satisfied`) |
| **Questioner** (`answer`) | beri **tanggapan manusiawi** atas jawaban lalu ajukan pertanyaan berikutnya |
| **Assessor** (`assess`) | verdict akhir, sadar cakupan tiap poin |

Node **Decide** (Code) di antara Monitor dan Questioner menerapkan logika: jika poin puas
**atau** sudah 5 pertanyaan pada poin itu (cap), maju ke poin berikutnya; bila poin terakhir
tuntas, `done: true`. Node **IF Done** mengarahkan ke Parse Done atau ke Questioner.

```
start  → Get Job → Planner → Parse Planner
answer → Get Job → Monitor → Decide → IF Done ┬ true  → Parse Done
                                              └ false → Questioner → Parse Question
assess → Get Job → Assessor → Parse Assess
```

## Alur (state machine 3 fase)

```
SETUP    upload CV + pilih lowongan nyata → call start
RUNNING  tampilkan tanggapan+pertanyaan → jawab → call answer (loop sampai done)
DONE     call assess → verdict + PDF
```

## Kontrak webhook

Semua request `mode: "interview"` pada webhook `job-assistant`, diteruskan Main Workflow ke
sub-workflow `6-interview.json` (node *Interview Pipeline*, Execute Workflow) dengan payload
sebagai objek `data`. Dibedakan oleh `action`.

### 0. Pemilihan lowongan — `mode: "search"` (reuse)

Setiap item `jobs` **wajib** menyertakan `job_id` (dipakai menarik `job_description`).

### 1. `action: "start"` — Planner

```json
// request
{ "mode":"interview", "action":"start",
  "cv_text":"<teks CV>", "job_id":"...", "position":"Data Analyst" }

// response
{ "cv_profile": {"current_role":"...","experience_years":2,"key_skills":["..."]},
  "plan": [ {"index":1,"point":"Pengalaman SQL & query kompleks","category":"technical"}, ... ],
  "total_points": 5,
  "current_point_index": 1,
  "question": "...", "category": "technical" }
```

### 2. `action: "answer"` — Monitor → Decide → Questioner

Streamlit mengirim state poin + seluruh riwayat (tiap item punya `point_index`).

```json
// request
{ "mode":"interview", "action":"answer", "job_id":"...",
  "cv_profile": {...}, "plan": [...], "total_points": 5,
  "current_point_index": 2, "point_qcount": 1,
  "history": [ {"question":"...","answer":"...","category":"...","point_index":1}, ... ] }

// response — lanjut
{ "done": false,
  "current_point_index": 3, "point_qcount": 1, "point_satisfied": true,
  "reaction": "Menarik, pendekatan imputasinya masuk akal.",
  "question": "Bagaimana kamu memastikan kualitas data sebelum analisis?",
  "category": "hr" }

// response — semua poin tuntas
{ "done": true, "current_point_index": 6, "total_points": 5 }
```

Streamlit memperbarui `current_point_index`/`point_qcount` dari response dan menghitung
progress dari rumus di atas — **tidak** mempercayai nilai progress dari agen.

### 3. `action: "assess"` — Assessor (FR-6.04)

```json
// request
{ "mode":"interview", "action":"assess", "job_id":"...",
  "cv_profile": {...}, "plan": [...], "history": [...] }

// response
{ "verdict": "Bisa Diterima", "score": 78,
  "reasons": [...], "strengths": [...], "improvements": [...],
  "per_question": [ {"question":"...","feedback":"...","score":8} ] }
```

## State di Streamlit (`st.session_state`)

| Key | Guna |
|---|---|
| `iv_stage` | `"setup"` / `"running"` / `"done"` |
| `iv_cv_text`, `iv_cv_profile` | CV & profil ringkas |
| `iv_job` | lowongan terpilih (`job_id`, `job_title`, `company_name`) |
| `iv_plan`, `iv_total_points` | rencana poin inti dari Planner |
| `iv_current_point_index`, `iv_point_qcount` | posisi & jumlah pertanyaan poin saat ini |
| `iv_history` | `[{question, answer, category, point_index, reaction}]` |
| `iv_current_q` | `{reaction, question, category}` yang menunggu jawaban |
| `iv_assessment` | hasil verdict akhir |

## Tampilan manusiawi (FR-6.02)

Questioner mengembalikan `reaction` (tanggapan singkat & spesifik atas jawaban terakhir) +
`question`. Streamlit menampilkannya sebagai satu gelembung: tanggapan (italik) lalu
pertanyaan — agar terasa seperti pewawancara sungguhan, bukan mesin penembak pertanyaan.

## Penanganan error & privasi

Semua panggilan lewat `call_n8n()` → error dikembalikan sebagai `{"error": <pesan ramah>}`
tanpa traceback (`NFR-3.02`). CV hanya diproses di memory; `cv_text` dikirim sekali di
`start`, giliran berikutnya cukup `cv_profile` (`NFR-5.01`).
