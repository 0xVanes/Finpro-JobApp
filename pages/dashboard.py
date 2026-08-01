import streamlit as st
from menu import menu_with_redirect
from db import engine
from sqlalchemy import text

st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

menu_with_redirect()

def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

def section_lbl(label, icon="📊"):
    st.markdown(f"### {icon} {label}")

username = st.session_state.username

st.markdown(f"## Selamat datang kembali, **{username}**")
st.write("")