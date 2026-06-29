import streamlit as st

def authenticated_menu():
    """Show navigation menu for authenticated users"""
    st.sidebar.header(f"👋 Welcome, {st.session_state.username}!")
    st.sidebar.caption(f"Role: {st.session_state.role}")
    st.sidebar.divider()
    
    st.sidebar.header("JobPath")
    
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