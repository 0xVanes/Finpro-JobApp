# JobChat - AI Job Chatbot (JobPath)

Dokumentasi fitur **Job Chat** (`FR-2.01`–`FR-2.04`). Menetapkan kontrak antara halaman Streamlit `pages/2jobchat.py` dan  Main Workflow `Main Workflow JobPath.json` di n8n.

## Prinsip desain
JobChat merupakan AI Job Chatbot yang membantu pengguna mencari informasi mengenai lowongan pekerjaan menggunakan Bahasa Indonesia dengan prinsip RAG sehingga LLM selalu menggambil referensi dari VectorDB sebelum menjawab.

Riwayat percakapan hanya disimpan selama sesi berjalan menggunakan `st.session_state (FR-1.02)` yaitu chat_history. Backend n8n bersifat `stateless (NFR-1.02)` sehingga tidak menyimpan riwayat percakapan.

## Arsitektur
```text
User Question
      │
      ▼
Chat Input (Streamlit)
      │
      ▼
call_n8n(mode="chat")
      │
      ▼
Main Workflow
      │
      ▼
Chat Agent (GPT-4o-mini)
      │
      ▼
Qdrant Vector Search (RAG)
      │
      ▼
Relevant Job Documents
      │
      ▼
AI Response
      │
      ▼
Streamlit Chat UI
```

## Kontrak webhook
Semua request dikirim ke endpoint `job-assistant` dengan:
Request:
```json
{
  "mode": "chat",
  "query": "Saya ingin menjadi Data Analyst."
}
```

Response:
```json
{
  "answer":"...",
  "jobs":[]
}
```

## Penanganan Error
Apabila backend gagal dipanggil atau LLM gagal menghasilkan jawaban, frontend hanya akan menampilkan pesan error tanpa traceback (`NFR-3.02`)

---

# Smart Search - Text-To-SQL (JobPath)
Dokumentasi fitur Smart Search (`FR-3.01`–`FR-3.05`). Menetapkan kontrak antara halaman Streamlit `pages/3smartsearch.py` dan Main Workflow `Main Workflow JobPath.json` di n8n.

## Prinsip desain
Smart Search menggunakan kombinasi **AI Agent** dan **SQL Tool**.

Pengguna menentukan filter pencarian, kemudian LLM membangun query SQL secara dinamis berdasarkan filter tersebut. Query dijalankan pada database MySQL sehingga hasil selalu berasal dari data lowongan yang sebenarnya.

Pendekatan ini menghilangkan kebutuhan membuat banyak query SQL manual.

## Arsitektur
```text
Search Filters
      │
      ▼
Streamlit
      │
      ▼
call_n8n(mode="search")
      │
      ▼
SQL Search Agent
      │
      ▼
Generate SQL
      │
      ▼
MySQL Tool
      │
      ├── Query daftar lowongan
      └── Query Top 5 kota
      │
      ▼
Format Response
      │
      ▼
Streamlit
```

## Fitur pencarian
Pengguna dapat menentukan kombinasi filter berikut:
- tipe pekerjaan
- posisi/keyword
- kota
- gaji minimum
- remote/hybrid

## Kontrak webhook
Request:
```json
{
    "mode":"search",
    "keyword":"Data Analyst",
    "work_type":"Full time",
    "city":"Jakarta",
    "salary_min":7000000,
    "hybrid_only":true
}
```
Response:
```json
{
  "jobs":[...],
  "top_cities":[
      {
          "city":"Jakarta",
          "count":24
      }
  ]
}
```

## Hasil
Frontend akan menunjukan daftar lowongan

## Error Handling
Bila AI menghasilkan JSON yang tidak valid, workflow akan melakukan parsing ulang dan mengembalikan pesan error

---
# CV Matcher - Career Recomendation Agent (JobPath)
Dokumentasi fitur CV Matcher (`FR-4.01`–`FR-4.04`). Menetapkan kontrak antara halaman Streamlit `pages/4cvmatcher.py` dan Main Workflow `Main Workflow JobPath.json` di n8n (mode=cv_match). Fitur ini akan berjalan bersamaan dengan fitur Career Path & Skill Gap (`FR-5.01`–`FR-5.05`) dan Sub Workflow `Sub Workflow Jobpath.json`

## Prinsip desain
CV tidak pernah disimpan permanen (`NFR-5.01`).
Setelah CV diunggah, sistem melakukan satu kali pemanggilan workflow n8n. Workflow tersebut menjalankan seluruh pipeline AI secara berurutan dengan career path classification, skill gap analysis, certification recommendation dan career roadmap

## Arsitektur
```text
Upload CV
      │
      ▼
Extract Text
      │
      ▼
call_n8n(mode="cv_match")
      │
      ▼
CV Matcher Agent
      │
      ▼
Qdrant Semantic Search
      │
      ▼
Top 3 Job Matching
      │
      ▼
Career Development Pipeline
      │
      ├── Career Path
      ├── Skill Gap
      ├── Certification
      └── Roadmap
      │
      ▼
Combined JSON
      │
      ▼
Streamlit
```

## Kontrak webhook
Request: 
```json
{
    "mode":"cv_match",
    "cv_text":"..."
}
```

Response:
```json
{
    "candidate_profile":{},
    "recommendations":[],
    "career_paths":[],
    "gap_analysis":[],
    "certifications":[],
    "career_roadmap":{}
}
```

## Frontend
Frontend akan memberikan response:
Profil Kandidat (`FR-4.02`)
- posisi terakhir
- pengalaman kerja
- skill utama

TOP 3 Job Recommendation (`FR-4.03`)
- nama pekerjaan yang cocok
- tempat kerja perusahaan tersebut
- kota perusahaan tersebut
- persentase kecocokan
- skill yang sudah ada
- skill yang belum ada
- masukan AI

Career Path (`FR-5.01`)
Menampilkan 5 jalur karir terbaik dengan confidence score dan alasan merekomendasikan jalur tersebut

Skill Gap (`FR-5.02`)
Untuk setiap jalur karir akan ditampilkan:
- skill yang sudah ada
- skill yang kurang
- prioritas pengembangan skill

Learning Recommendation (`FR-5.04`)
Menampilkan:
- sertifikasi yang dapat dimiliki
- situs kursus
- prioritas pengembangan skill

Roadmap menuju analisis data (`FR-5.05`)
Akan ditampilkan rencana karir untuk 0-3 bulan, 3-6 bulan dan 6-12 bulan.

---

# Market Insight Dashboard (JobPath)
Dokumentasi fitur Market Insight (`FR-7.01`-`FR-7.02`)

## Prinsip desain
Berbeda dengan fitur-fitur lainnya, dashboard ini **tidak menggunakan LLM**

Seluruh data diperoleh langsung melalui query SQL terhadap database `jobs.jsonl` yang sudah dibersihkan dan diolah dan dimasukan ke SQL sehingga data yang ditampilkan merepresentasikan kondisi data aktual.

## Arsitektur
MySQL
   │
   ├── Demand Query
   ├── Salary Query
   ▼
Pandas
   ▼
Plotly
   ▼
Dashboard

## Query SQL
Hot Demand (`FR-7.01`):
SQL menghitung jumlah lowongan berdasarkan `job_title`
```SQL
SELECT job_title,
COUNT(*)
FROM jobs
GROUP BY job_title
ORDER BY COUNT(*) DESC;
```
Hasil divisualisasikan menggunakan horizontal bar chart dari Plotly

Salary Distribution (`FR-7.02`):
SQL mengambil posisi `salary_min` dan `salary_max` untuk menunjukan rentang gaji yang dapat didapatkan oleh user.

Tabel tambahan dimasukan untuk menunjukan demand dari pekerjaan tersebut dengan status tinggi bila lebih atau sama dengan 20, sedang 10-19 dan rendah <10.

## Error Handling
Apabila koneksi MySQL gagal, dashboard tidak akan menunjukan visualisasi dan menampilkan pesan gagal koneksi saja tanpa menampilkan informasi konfigurasi database.