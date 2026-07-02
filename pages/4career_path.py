import streamlit as st
from menu import menu_with_redirect

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Career Path", layout="wide")

# Load menu
menu_with_redirect()

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## Webhook CV


## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="career-header">
  <div class="emoji-bg">🛤️</div>
  <h1>Career Path Visualizer</h1>
  <p class="sub">Peta jalur karir</p>
  <div class="badge-row">
    <span>Visualisasi jalur (FR-5.01)</span>
  </div>
</div>
""", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)
# ambil data dari CV dan LLM
with col1:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">📊</div>
    <h3 class="career-title">Job Exp</h3>
    <div class="career-job">Bidang</div>
</div>""", unsafe_allow_html=True)
    
with col2:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">🎯</div>
    <h3 class="career-title">Job Level</h3>
    <div class="career-job">Level</div>
</div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="career-card">
    <div class="career-icon">📈</div>
    <h3 class="career-title">3 tahap</h3>
    <div class="career-job">Ke Depan</div>
</div>""", unsafe_allow_html=True)

## ISI DARI Hasil LLM
st.markdown(f"""<div class="salary-info">💡 Jalur: </div>""", unsafe_allow_html=True)
st.divider()
