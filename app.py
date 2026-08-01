import streamlit as st
from dotenv import load_dotenv, find_dotenv
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os
from pathlib import Path
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(find_dotenv(), override=True)
ROOT = Path(dotenv_path).resolve().parent if dotenv_path else Path.cwd()

st.set_page_config(page_title="FinPRO-JOB 👩🏻‍💻🧑🏻‍💻💼🔎", layout="wide")

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

## Load SQL
def resolve_path(p):
    """Resolusikan path relatif terhadap root repo (bukan cwd notebook)."""
    p = Path(p)
    return p if p.is_absolute() else (ROOT / p)

mysql_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    database=os.getenv("MYSQL_DATABASE"),
)
engine = create_engine(mysql_url)

# Uji koneksi cepat
with engine.connect() as c:
    print("MySQL  :", c.execute(text("SELECT VERSION()")).scalar())

## Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


## Verify credentials
def hash_password(password:str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_credentials(username, password):
    """Verify username and password"""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                            text("SELECT password_hash, role FROM user_data WHERE username = :username"),
                            {"username": username}
                        )
            row = result.mappings().fetchone()
    except Exception as e:
        st.error(f"Error verifikasi username dan password")
        return False, None
    if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return True, row["role"]
    return False, None

def create_user(username: str, password: str, role: str = "user")->tuple[bool, str]:
    """Create a new user account"""
    if not username or not password:
        return False, "Username dan password wajib diisi"
    if len(password) < 8:
        return False, "Password minimal 8 karakter"

    try:
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT 1 FROM user_data WHERE username = :username"),
                {"username": username}
            ).fetchone()
            if existing:
                return False, "Username sudah digunakan"

            conn.execute(
                text("INSERT INTO user_data (username, password_hash, role) VALUES (:username, :password_hash, :role)"),
                {"username": username, "password_hash": hash_password(password), "role": role}
            )
    except Exception as e:
        return False, f"Error database: {e}"

    return True, "Akun berhasil dibuat"

## Login/Signup page
def login_page():
    """Display the login page"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""## 👩🏻‍💻🧑🏻‍💻 FinPRO-JOBPath""")
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Masukkan username")
                password = st.text_input("Password", placeholder="Masukkan password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)

                if submit:
                    if not username or not password:
                        st.error("⚠️ Masukkan username dan password")
                    else:
                        is_valid, role = verify_credentials(username, password)
                        if is_valid:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.role = role
                            st.rerun()
                        else:
                            st.error("❌ Username atau password tidak valid")

        with tab_signup:
            with st.form("signup_form", clear_on_submit=True):
                new_username = st.text_input("Username", placeholder="Isi username")
                new_password = st.text_input("Password", type="password", placeholder="Isi password")
                confirm_password = st.text_input("Konfirmasi password", type="password")
                signup_submit = st.form_submit_button("Buat akun", use_container_width=True)

                if signup_submit:
                    if new_password != confirm_password:
                        st.error("❌ Password tidak sesuai")
                    else:
                        success, message = create_user(new_username, new_password)
                        if success:
                            st.success(f"✅ {message}. Anda dapat login sekarang.")
                        else:
                            st.error(f"⚠️ {message}")

## Check if user is authenticated
if st.session_state.authenticated:
    st.switch_page("pages/dashboard.py")
else:
    login_page()