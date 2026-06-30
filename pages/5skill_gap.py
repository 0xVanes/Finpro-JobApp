import streamlit as st
from menu import menu_with_redirect

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

# Load menu
menu_with_redirect()

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()