import streamlit as st

## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

def authenticated_menu():
    """Show navigation menu for authenticated users"""
    st.sidebar.header(f"👋 Welcome, {st.session_state.username}!")
    st.sidebar.caption(f"Role: {st.session_state.role}")

    st.sidebar.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:15px;">
    <div style="width:48px; height:48px; border-radius:14px;
        background:linear-gradient(135deg,#7C6CFF,#59D6D6);
        color:white; display:flex; align-items:center; justify-content:center;
        font-size: 30px; font-weight:900;">JP
    </div>
    <div>
        <div style = "font-size:20px;"> <b> JobPath </b> </div>
        <div> Career Navigator </div>
    </div>
    
</div> """, unsafe_allow_html=True)

    st.sidebar.divider()
    
    st.sidebar.header("Menu")
    
    # Using page_link
    st.sidebar.page_link("pages/1job_chat.py", label="💬 Job Chat")
    st.sidebar.page_link("pages/2smart_search.py", label="🔍 Smart Search")
    st.sidebar.page_link("pages/3cv_matcher.py", label="📄 CV Matcher")
    st.sidebar.page_link("pages/4career_path.py", label="🛤️ Career Path")
    st.sidebar.page_link("pages/5skill_gap.py", label="🎯 Skill Gap")
    st.sidebar.page_link("pages/6interview.py", label="🎤 Interview")
    st.sidebar.page_link("pages/7market.py", label="📊 Market")
    
    # Logout button
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

def unauthenticated_menu():
    """Show navigation menu for unauthenticated users"""
    st.sidebar.header("JobPath")
    st.sidebar.info("👋 Please login to access all features")
    if st.sidebar.button("🔑 Login", use_container_width=True):
        st.switch_page("app.py")

def menu():
    """Main menu function to determine which menu to show"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        authenticated_menu()
    else:
        unauthenticated_menu()

def menu_with_redirect():
    """Redirect to login if not authenticated, then show menu"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.switch_page("app.py")
    else:
        menu()