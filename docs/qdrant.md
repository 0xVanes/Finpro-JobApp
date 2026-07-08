# Vector Database — Qdrant (JobPath)

Dokumentasi collection Qdrant yang dibuat oleh `notebooks/data_ingestion.ipynb`,
dipakai untuk RAG (`FR-2.02`) dan CV Matcher (`FR-4.03`).

## Collection `jobs`

| Properti | Nilai |
|---|---|
| Nama | `jobs` (dari `QDRANT_COLLECTION`) |
| Ukuran vektor | **1536** (OpenAI `text-embedding-3-small`) |
| Distance | **Cosine** |
| Titik per lowongan | **1** (tanpa chunking) |
| `point_id` | `job_id` (UUID5, sama dengan PK MySQL) |

**Tanpa chunking:** eksplorasi menunjukkan `job_description` terpanjang ~2.352 token,
jauh di bawah batas 8.191 token model embedding. Maka setiap lowongan cukup menjadi
satu vektor — lebih sederhana dan metadata tetap rapi.

## Teks yang di-embed

Gabungan **`job_title` + `job_description`**:

```
{job_title}
{job_description}
```

Judul disertakan karena query pengguna sering menyebut nama peran ("data analyst",
"HR staff") sementara deskripsi tidak selalu mengulang nama posisi secara eksplisit.

Teks yang sama juga **disimpan apa adanya di payload `content`** (via `build_content`
pada notebook) sehingga satu sumber teks dipakai untuk embedding sekaligus dibaca
kembali oleh retriever — lihat bagian Payload.

## Payload

Payload menyimpan **teks dokumen** untuk RAG sekaligus **field terstruktur** untuk
filter hybrid. Strukturnya mengikuti format node **Qdrant Vector Store** di n8n
(LangChain), yang membaca `content` sebagai isi dokumen dan `metadata` sebagai
atributnya:

| Key | Tipe | Guna |
|---|---|---|
| `content` | string | **Teks dokumen** (`job_title` + `job_description`) — isi yang dibaca agent RAG di n8n; identik dengan teks yang di-embed |
| `metadata` | object | Salinan seluruh field terstruktur di bawah — dibaca LangChain sebagai metadata dokumen |

> **Penting:** tanpa `content`, retriever LangChain menerima dokumen tanpa teks,
> sehingga agent RAG selalu menjawab "tidak ditemukan" meski vektornya cocok.
> Field `content`/`metadata` adalah **kontrak** yang dibaca workflow n8n — bila
> notebook di-ingest ulang, keduanya harus tetap dihasilkan `make_payload`.

Field terstruktur juga di-**flatten** di level atas payload (di luar `metadata`)
agar bisa dipakai langsung sebagai `query_filter` Qdrant tanpa menembus objek:

| Field | Tipe | Guna |
|---|---|---|
| `job_id` | string | jembatan ke MySQL |
| `job_title` | string | tampilan hasil |
| `company_name` | string / null | tampilan |
| `city` | string / null | filter lokasi |
| `province` | string | filter lokasi |
| `work_type` | string | filter tipe pekerjaan |
| `work_arrangement` | string | filter Onsite/Hybrid/Remote |
| `seniority_level` | string / null | filter/ranking senioritas |
| `salary_min` | int | filter gaji |
| `salary_max` | int | filter gaji |
| `is_salary_estimated` | bool | menandai gaji hasil estimasi model |

Contoh payload satu titik:

```json
{
  "content": "Social Media Specialist\nKey Responsibilities: Merancang strategi ...",
  "metadata": {
    "job_id": "0052b191-...", "job_title": "Social Media Specialist",
    "company_name": "PT Vita Shopindo", "city": "Jakarta Barat", "province": "Jakarta Raya",
    "work_type": "Full-time", "work_arrangement": "Onsite", "seniority_level": "Senior",
    "salary_min": 6666666, "salary_max": 7777777, "is_salary_estimated": false
  },
  "job_id": "0052b191-...", "job_title": "Social Media Specialist", "city": "Jakarta Barat"
}
```

> Field terstruktur muncul dua kali: di dalam `metadata` (untuk LangChain) dan
> di level atas (untuk `query_filter`). Contoh di atas dipersingkat pada bagian flat.

## Idempotency & resume

- **Idempotency** — `point_id = job_id` yang deterministik; `upsert` dengan id sama
  menimpa titik lama, sehingga run ulang **tidak menggandakan** data.
- **Resume** — sebelum embedding, seluruh `job_id` yang sudah ada di collection diambil
  (`scroll`), lalu hanya lowongan yang belum ada yang di-embed & di-upsert per batch
  (`INGEST_BATCH_SIZE`). Bila proses gagal di tengah, run berikutnya melanjutkan dari
  yang belum masuk — **biaya embedding tidak terbuang** untuk yang sudah selesai.

## Contoh pencarian (dari notebook)

```python
qvec = embed_texts(["data analyst berpengalaman di Jakarta"])[0]
hits = qc.query_points("jobs", query=qvec, limit=5, with_payload=True).points
```

Untuk pencarian hybrid (semantik + filter), sertakan `query_filter`, mis. hanya
lowongan dengan `work_arrangement = "Remote"` atau `salary_min >= 10_000_000`.

## Konfigurasi

Kredensial dibaca dari `.env` (lihat `.env.example`): `QDRANT_URL`, `QDRANT_API_KEY`,
`QDRANT_COLLECTION`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`.
