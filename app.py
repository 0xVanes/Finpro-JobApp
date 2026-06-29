import streamlit as st
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

st.set_page_config(page_title="FinPRO-JOB 👩🏻‍💻🧑🏻‍💻💼🔎", layout="wide")

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()


## Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


## Verify credentials
def verify_credentials(username, password):
    """Verify username and password"""
    valid_users = {
        "admin": {"password": "admin12345",
                "role": "admin"},
        "user": {"password": "user123",
                "role": "user"}}
    
    if username in valid_users:
        if password == valid_users[username]["password"]:
            return True, valid_users[username]["role"]
    return False, None

## Login page
def login_page():
    """Display the login page"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""## 👩🏻‍💻🧑🏻‍💻 FinPRO-JOBPath""")
        
        with st.container():
            st.markdown("### Login to your account")
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="username_input"
                )
                
                password = st.text_input(
                    "Password",
                    placeholder="Enter your password",
                    type="password",
                    key="password_input"
                )
                
                submit = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                )
                
                if submit:
                    if not username or not password:
                        st.error("⚠️ Please enter both username and password")
                    else:
                        is_valid, role = verify_credentials(username, password)
                        if is_valid:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.role = role
                            st.rerun()  # Refresh to show main app
                        else:
                            st.error("❌ Invalid username or password")

## Check if user is authenticated
if st.session_state.authenticated:
    st.switch_page("pages/1job_chat.py")
else:
    login_page()