import streamlit as st
from menu import menu_with_redirect

from utils import call_n8n, job_card, section_lbl, show_error, TIMEOUT_SQL

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Smart Search", layout="wide")

# Load menu
menu_with_redirect()


## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="search-header">
  <div class="emoji-bg">🔍</div>
  <h1>Smart Search</h1>
  <p class="sub">Filter presisi + 5 kota terbaik untuk posisi targetmu</p>
  <div class="badge-row">
    <span>Range gaji (FR-3.02)</span>
    <span>Tipe kerja (FR-3.03)</span>
    <span>Top 5 kota (FR-3.05)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filter criteria (FR-3.01) ────────────────────────────────────
section_lbl("Kriteria Pencarian", "🎯")

col1, col2, col3 = st.columns(3)
with col1:
    keyword = st.text_input("Posisi / kata kunci", placeholder="Data Analyst")
with col2:
    work_type_options = [
        "Semua", "Full time", "Kontrak/Temporer",
        "Paruh waktu", "Remote", "Internship",
    ]
    work_type = st.selectbox("Tipe kerja (FR-3.03)", work_type_options)
with col3:
    city = st.text_input("Kota (FR-3.04)", placeholder="Jakarta")

col4, col5 = st.columns(2)
with col4:
    # FR-3.02: range gaji
    salary_min = st.number_input(
        "Gaji minimum (Rp)",
        min_value=0,
        max_value=100_000_000,
        step=1_000_000,
        value=0,
        help="0 = tidak ada filter gaji minimum",
    )
with col5:
    st.write("")
    hybrid_only = st.checkbox("Hanya Remote / Hybrid")

search_clicked = st.button("🔍 Cari Lowongan", use_container_width=True)

if not search_clicked:
    st.info("Atur filter di atas dan klik **Cari Lowongan**.")
    st.stop()

# ── Proses pencarian ─────────────────────────────────────────────
with st.spinner("Menyaring lowongan..."):
    result = call_n8n(
        payload={
            "mode":        "search",
            "keyword":     keyword or None,
            "work_type":   None if work_type == "Semua" else work_type,
            "city":        city or None,
            "salary_min":  salary_min if salary_min > 0 else None,
            "hybrid_only": hybrid_only,
        },
        timeout=TIMEOUT_SQL,
    )

if "error" in result:
    show_error(result["error"])
    st.stop()

jobs       = result.get("jobs", [])
top_cities = result.get("top_cities", [])

# FR-3.05: Top 5 kota terbaik
if top_cities:
    section_lbl("Top 5 Kota Terbaik (FR-3.05)", "📍")
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    city_chips = " ".join(
        f'<span class="chip has">'
        f'{medals[i]} {c["city"]} <b>{c["count"]}</b></span>'
        for i, c in enumerate(top_cities[:5])
    )
    st.markdown(city_chips, unsafe_allow_html=True)
    st.write("")

# Hasil lowongan
if not jobs:
    st.info("Tidak ada lowongan yang cocok dengan filter ini. Coba perluas kriteria.")
    st.stop()

st.success(f"✓ Ditemukan {len(jobs)} lowongan")
for job in jobs:
    job_card(job)
