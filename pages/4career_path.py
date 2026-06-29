import streamlit as st
from menu import menu_with_redirect

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Dashboard", layout="wide")

# Load menu
menu_with_redirect()