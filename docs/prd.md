# Product Requirements Document (PRD): Daftar Kebutuhan Lengkap

Produk: JobPath (Career Navigator)

Fase: Brainstorming & Requirements Gathering

## A. FUNCTIONAL REQUIREMENTS (Kebutuhan Fungsional)

Apa yang sistem HARUS BISA lakukan berdasarkan fitur dan interaksi pengguna.

### 1. Interaksi & Antarmuka Utama (Streamlit)

FR-1.01: Sistem harus memiliki sidebar navigasi untuk berpindah antar menu fitur (Job Chat, Search, CV, dll).

FR-1.02: Sistem harus menyimpan riwayat percakapan (chat history) pengguna selama sesi aktif di aplikasi.

FR-1.03: Sistem harus menampilkan indikator loading (spinner/progress bar) saat N8N sedang memproses data.

### 2. Fitur: Job Chat / Natural Language Search (Syarat Utama - RAG)

FR-2.01: Pengguna dapat mengetikkan pertanyaan berbasis teks ke chatbot.

FR-2.02: Sistem harus merespons pertanyaan pengguna terkait job description, kualifikasi, dan tanggung jawab pekerjaan menggunakan data dari Qdrant (Vector DB).

FR-2.03: Sistem harus mampu menangani pertanyaan di luar konteks pekerjaan dengan memberikan pesan error yang sopan ("Saya hanya agen pencari kerja...").

FR-2.04: Sistem harus memberi jawaban percakapan chat dalam bahasa Indonesia.

### 3. Fitur: Smart Search / Pencarian Terstruktur (Syarat Utama - SQL)

FR-3.01: Pengguna dapat mencari pekerjaan berdasarkan input spesifik menggunakan dropdown atau slider.

FR-3.02: Sistem dapat memfilter berdasarkan Range Gaji.

FR-3.03: Sistem dapat memfilter berdasarkan Tipe Pekerjaan (Full-time, Intern, Remote, dll).

FR-3.04: Sistem dapat memfilter berdasarkan Lokasi.

FR-3.05: Sistem (SQL Agent) harus menampilkan 5 rekomendasi daerah/lokasi terbaik untuk suatu pekerjaan. (Dari ide Brainstorm)

### 4. Fitur: Analisis CV & Rekomendasi (Syarat Lanjut)

FR-4.01: Sistem memungkinkan pengguna mengunggah file CV (PDF/DOCX).

FR-4.02: Sistem secara otomatis mengekstrak informasi skill, pengalaman, dan pendidikan dari CV (Profiling User).

FR-4.03: Sistem mencocokkan profil CV pengguna dengan database lowongan dan menampilkan Top 3 Pekerjaan yang paling relevan (CV Matcher).

FR-4.04: Sistem memberikan alasan singkat mengapa pekerjaan tersebut direkomendasikan berdasarkan skill di CV.

### 5. Fitur: Career Path & Skill Gap (Blueprint & Brainstorm)

FR-5.01: Sistem dapat memvisualisasikan jalur karir (Career Path) pengguna dari posisinya saat ini hingga beberapa tingkat di atasnya.

FR-5.02: Sistem dapat menganalisis skill yang kurang (Skill Gap) dari pengguna dibandingkan dengan permintaan pasar untuk posisi yang diincarnya.

FR-5.03: Sistem dapat memberikan rekomendasi skill yang harus dikembangkan.

FR-5.04: Sistem dapat memberikan rekomendasi tautan/situs pembelajaran atau sertifikasi spesifik untuk menutup Skill Gap tersebut.

### 6. Fitur: Simulasi Wawancara (Brainstorming)

FR-6.01: Pengguna dapat memilih mode "Latihan Interview" untuk posisi tertentu.

FR-6.02: AI Agent memberikan pertanyaan wawancara (teknis/HR) satu per satu kepada pengguna.

FR-6.03: Sistem menerima jawaban teks dari pengguna.

FR-6.04: Di akhir simulasi, sistem memberikan prediksi/rekomendasi apakah kandidat "Bisa Diterima" atau "Tidak", beserta alasannya.

FR-6.05: User dapat mendownload hasil transkrip dari wawancara dan penilaian dari AI agent

### 7. Fitur: Market Insight & Visualisasi Data Dalam Dashboard (Blueprint & Brainstorm)

FR-7.01: Sistem menampilkan visualisasi statistik/grafik skill pekerjaan yang sedang banyak dicari (Hot Demand Job).

FR-7.02: Sistem menampilkan grafik distribusi gaji rata-rata berdasarkan bidang pekerjaan.

### 8. Fitur: Manajemen Data Tambahan & Komunitas (Brainstorming)

FR-8.01: Sistem memiliki ML Model tersendiri (Regresi) untuk memprediksi dan mengisi nilai gaji yang kosong (None) pada dataset, sehingga rentang gaji selalu tersedia.

FR-8.02: Sistem dapat membuat/generate desain CV (Auto-generate CV) berdasarkan profil pengguna, yang bisa diunduh sebagai PDF.

FR-8.03: Pengguna dapat menambahkan data lowongan pekerjaan baru (Add Data Job) ke dalam database SQL.

## B. NON-FUNCTIONAL REQUIREMENTS (Kebutuhan Non-Fungsional)

Syarat teknis, performa, batasan, dan kualitas sistem (Penting untuk rubrik penilaian).

### 1. Arsitektur & Teknologi (Wajib dari Purwadhika)

NFR-1.01: Sistem wajib dibangun menggunakan arsitektur Multi-Agent yang diorkestrasi di N8N.

NFR-1.02: Sistem wajib di-deploy sebagai REST API melalui node Webhook pada N8N.

NFR-1.03: Sistem wajib menggunakan Vector Database (Qdrant) untuk keperluan Retrieval-Augmented Generation (RAG).

NFR-1.04: Sistem wajib menggunakan Relational Database (MySQL) yang diakses oleh SQL Agent.

NFR-1.05: Antarmuka (Front-end) wajib menggunakan Streamlit.

### 2. Performa & Waktu Respons (Performance)

NFR-2.01: Waktu respons dari agen RAG untuk menjawab pertanyaan chat maksimal tidak boleh lebih dari 15 detik.

NFR-2.02: Pencarian filter SQL harus mengembalikan data ke UI Streamlit dalam waktu maksimal 5 detik.

NFR-2.03: Proses ekstraksi PDF CV tidak boleh memakan waktu lebih dari 30 detik untuk mencegah Webhook Timeout di N8N.

### 3. Usability & User Experience (Penilaian 10% di Rubrik)

NFR-3.01: Antarmuka harus rapi, intuitif, dan tidak membingungkan pengguna baru.

NFR-3.02: Sistem harus memberikan penanganan kesalahan (Error Handling) yang jelas jika API N8N mati, database terputus, atau format CV tidak didukung. Tidak boleh muncul pesan traceback error Python yang mentah ke pengguna.

### 4. Kualitas Kode (Penilaian Individu 10% di Rubrik)

NFR-4.01: Kode Streamlit harus modular (dipisah per menu/halaman) agar mudah di-maintain.

NFR-4.02: Modul kode harus memiliki comment atau docstring yang jelas.

NFR-4.03: Konfigurasi kredensial (API Key OpenAI, Database URL) harus disimpan dalam file .env (environment variables) dan tidak boleh di-hardcode di dalam kode utama.

### 5. Keamanan & Privasi

NFR-5.01: Data CV yang diunggah pengguna hanya diproses di dalam memory selama sesi berlangsung dan tidak disimpan secara permanen di server publik (menghindari kebocoran data pribadi).
