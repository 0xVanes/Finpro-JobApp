import streamlit as st
import requests
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
load_dotenv(find_dotenv(), override=True)

st.set_page_config(page_title="FinPRO-JOB 👩🏻‍💻🧑🏻‍💻💼🔎", layout="wide")
st.title("FinPRO-JOB")

n8n_url = "https://n8n-student.purwadhika.com/webhook/finproJOB"
respond = requests.post(n8n_url)
print(respond.status_code)
print(dict(respond.headers))
print(respond.text)