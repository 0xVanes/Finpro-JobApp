import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
load_dotenv(find_dotenv(), override=True)