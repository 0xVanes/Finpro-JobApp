import streamlit as st
from menu import menu_with_redirect

from utils import call_n8n, job_card, show_error, TIMEOUT_CHAT, init_session_state

# Page configuration
st.set_page_config(page_title="FinPRO-JOB - Job Chat", layout="wide")

# Load menu
menu_with_redirect()


## Loading CSS
def load_css():
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
load_css()

init_session_state()

## ---------- FRONTEND STARTS HERE
st.markdown("""
<div class="chat-header">
  <div class="emoji-bg">💬</div>
  <h1>Job Chat</h1>
  <p class="sub">Tanya apa saja tentang lowongan kerja dalam Bahasa Indonesia</p>
  <div class="badge-row">
    <span>Bahasa Indonesia (FR-2.04)</span>
    <span>RAG · Qdrant (FR-2.02)</span>
    <span>Riwayat sesi (FR-1.02)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# FR-1.02: Tampilkan riwayat percakapan sesi ini
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# FR-2.01: Input chat
prompt = st.chat_input("Tanya seputar lowongan kerja...")

if prompt:
    # Simpan dan tampilkan pesan user
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # FR-1.03: Spinner saat N8N memproses
    with st.chat_message("assistant"):
        with st.spinner("Mencari jawaban..."):
            result = call_n8n(
                payload={"mode": "chat", "query": prompt},
                timeout=TIMEOUT_CHAT,
            )

        if "error" in result:
            # NFR-3.02: pesan error ramah, tidak ada traceback
            show_error(result["error"])
        else:
            answer = result.get("answer", "")

            # FR-2.03: out-of-context dijawab N8N dengan pesan sopan
            if answer:
                st.markdown(answer)
            else:
                st.info("Tidak ada jawaban yang dikembalikan dari server.")

            # Tampilkan kartu lowongan jika ada
            for job in result.get("jobs", []):
                job_card(job)

            # Simpan ke history (hanya jawaban teks, bukan kartu)
            if answer:
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

# Tombol bersihkan riwayat
if st.session_state.chat_history:
    if st.button("🗑️ Hapus riwayat", use_container_width=False):
        st.session_state.chat_history = []
        st.rerun()
