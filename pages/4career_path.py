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

st.markdown("""
<div class="career-header">
  <div class="emoji-bg">🛤️</div>
  <h1>Career Path Visualizer</h1>
  <p class="sub">Peta jalur karir + gap skill + link sertifikasi spesifik</p>
  <div class="badge-row">
    <span>Visualisasi jalur (FR-5.01)</span>
    <span>Gap analysis (FR-5.02)</span>
    <span>Link belajar (FR-5.04)</span>
  </div>
</div>
""", unsafe_allow_html=True)