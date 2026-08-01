import streamlit as st
from menu import menu_with_redirect
from db import engine
from sqlalchemy import text
import pandas as pd

st.set_page_config(page_title="FinPRO-JOB - Monitoring", layout="wide")

menu_with_redirect()

def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

def section_lbl(label, icon="📊"):
    st.markdown(f"### {icon} {label}")

## FRONT-END STARTS HERE
if st.session_state.get("role") != "admin":
    st.error("🚫 Halaman ini hanya dapat diakses oleh admin.")
    st.stop()

st.markdown("## 🛠️ Monitoring Sistem")
st.caption("Dashboard internal untuk memantau kesehatan dan penggunaan aplikasi FinPRO-JOB.")
st.write("")

## Ambil data user
@st.cache_data(ttl=30)
def fetch_users():
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT username, role, created_at FROM user_data ORDER BY created_at DESC")
        ).mappings().fetchall()
    return pd.DataFrame(rows)

try:
    users_df = fetch_users()
except Exception as e:
    st.error(f"Gagal memuat data monitoring: {e}")
    st.stop()

## Berapa pengguna
total_users = len(users_df)

c1, _ = st.columns(2)
c1.metric("👥 Total Pengguna", total_users)

st.write("")

## N8N-Health
section_lbl("Status Koneksi N8N", "🔌")
import os
import requests

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

col_status, col_btn = st.columns([3, 1])
with col_btn:
    check_clicked = st.button("🔄 Cek Status Sekarang", use_container_width=True)

with col_status:
    if check_clicked:
        if not N8N_WEBHOOK_URL:
            st.warning("⚠️ N8N_WEBHOOK_URL belum dikonfigurasi.")
        else:
            try:
                resp = requests.head(N8N_WEBHOOK_URL, timeout=5)
                if resp.status_code < 500:
                    st.success(f"✅ N8N merespons (HTTP {resp.status_code})")
                else:
                    st.error(f"❌ N8N mengembalikan error (HTTP {resp.status_code})")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Tidak dapat terhubung ke N8N: {e}")
    else:
        st.caption("Klik tombol untuk memeriksa status koneksi ke webhook N8N.")

st.write("")

## Pendaftaran pengguna
section_lbl("Pendaftaran Pengguna dari Waktu ke Waktu", "📈")
if not users_df.empty:
    signups = users_df.copy()
    signups["created_at"] = pd.to_datetime(signups["created_at"]).dt.date

    # Hitung jumlah pendaftaran per hari, lalu jumlahkan secara kumulatif
    daily_counts = signups.groupby("created_at").size().sort_index()
    cumulative_counts = daily_counts.cumsum()

    # Pastikan grafik dimulai dari 0 pada hari sebelum pendaftaran pertama
    first_date = cumulative_counts.index.min()
    start_date = first_date - pd.Timedelta(days=1)
    cumulative_counts = pd.concat([
        pd.Series([0], index=[start_date]),
        cumulative_counts
    ])

    st.line_chart(cumulative_counts)
else:
    st.info("Belum ada data pendaftaran.")

## Daftar user
section_lbl("Daftar Pengguna Terdaftar", "👥")
if not users_df.empty:
    display_users = users_df.copy()
    display_users["created_at"] = pd.to_datetime(display_users["created_at"]).dt.strftime("%d %b %Y, %H:%M")
    st.dataframe(
        display_users.rename(columns={
            "username": "Username", "role": "Role", "created_at": "Terdaftar Sejak"
        }),
        use_container_width=True, hide_index=True
    )
else:
    st.info("Belum ada pengguna terdaftar.")

st.write("")