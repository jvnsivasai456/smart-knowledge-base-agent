import streamlit as st
import requests
import os
import json
import base64

# API Host configuration
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")

# Mobile PWA Manifest
pwa_manifest = {
    "name": "Smart Knowledge Base",
    "short_name": "SmartKB",
    "description": "Smart Knowledge Base AI Chatbot",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0E1117",
    "theme_color": "#4F46E5",
    "orientation": "portrait",
    "icons": [
        {
            "src": "https://api.iconify.design/fluent-emoji:brain.svg",
            "sizes": "192x192 512x512",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }
    ]
}
manifest_b64 = base64.b64encode(json.dumps(pwa_manifest).encode('utf-8')).decode('utf-8')

# Streamlit Page Config
st.set_page_config(
    page_title="Smart KB",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"  # Mobile friendly: start collapsed so chat is front and center
)

# Mobile-First Progressive Web App Styling & Headers
st.markdown(f"""
<head>
  <!-- Mobile PWA Meta Tags -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="SmartKB">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="theme-color" content="#4F46E5">
  <link rel="manifest" href="data:application/manifest+json;base64,{manifest_b64}">
  <link rel="apple-touch-icon" href="https://api.iconify.design/fluent-emoji:brain.svg">
</head>
<style>
/* Remove website chrome for native app look */
#MainMenu {{visibility: hidden; display: none;}}
footer {{visibility: hidden; display: none;}}
header {{visibility: hidden; display: none;}}
.stDeployButton {{display: none;}}
[data-testid="stToolbar"] {{visibility: hidden; display: none;}}
[data-testid="stDecoration"] {{display: none;}}

/* Mobile app touch optimizations */
* {{
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}}

/* Clean mobile layout & spacing */
.block-container {{
  padding-top: 1rem !important;
  padding-bottom: 5rem !important;
  padding-left: 0.75rem !important;
  padding-right: 0.75rem !important;
  max-width: 900px !important;
  margin: 0 auto !important;
}}

/* Mobile-styled floating chat input bar */
[data-testid="stBottomBlockContainer"] {{
  padding-bottom: env(safe-area-inset-bottom, 1rem) !important;
  background: rgba(14, 17, 23, 0.95) !important;
  backdrop-filter: blur(10px) !important;
}}

/* Native App button touch targets */
button {{
  min-height: 42px !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
}}

/* Chat message bubbles */
[data-testid="stChatMessage"] {{
  border-radius: 16px !important;
  padding: 0.75rem 1rem !important;
  margin-bottom: 0.75rem !important;
}}

/* Responsive typography */
@media (max-width: 768px) {{
  h1 {{ font-size: 1.5rem !important; }}
  p, span, div {{ font-size: 0.95rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# Check Backend Health
api_healthy = False
try:
    health_resp = requests.get(f"{API_HOST}/health", timeout=2)
    if health_resp.status_code == 200:
        api_healthy = True
except Exception:
    api_healthy = False

# App Bar / Top Navigation
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("### 🧠 Smart KB Chatbot")
with col_status:
    if api_healthy:
        st.markdown("<span style='color:#10B981;font-size:12px;font-weight:600;'>🟢 Online</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#EF4444;font-size:12px;font-weight:600;'>🔴 Offline</span>", unsafe_allow_html=True)

# Mobile-Friendly Document Ingestion Panel (Expandable at top for quick phone access)
with st.expander("📤 Upload & Manage Documents", expanded=False):
    uploaded_file = st.file_uploader(
        "Choose file (PDF, DOCX, TXT):",
        type=["pdf", "docx", "txt"],
        key="main_uploader"
    )
    if st.button("🚀 Upload & Index Document", use_container_width=True):
        if uploaded_file and api_healthy:
            with st.spinner(f"Indexing {uploaded_file.name}..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    res = requests.post(f"{API_HOST}/upload", files=files, timeout=30)
                    if res.status_code == 200:
                        st.success(f"✅ Indexed **{uploaded_file.name}** into ChromaDB!")
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        elif not uploaded_file:
            st.warning("Please select a file first.")
        else:
            st.error("API server is offline.")

# Sidebar Settings (For Desktop or tablet users)
with st.sidebar:
    st.header("⚙️ App Settings")
    top_k = st.slider("Retrieve Top-K Chunks:", min_value=1, max_value=8, value=4)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    st.subheader("📱 Open on Phone")
    qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mobile_qr.png")
    if os.path.exists(qr_path):
        st.image(qr_path, caption="Scan with camera to install", use_container_width=True)
    st.caption("Link: http://192.168.1.53:8501")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to Smart KB!**\n\nI am your mobile knowledge base assistant. Tap **📤 Upload & Manage Documents** above to add files, or ask me any question!",
            "sources": []
        }
    ]

# Display Chat Messages
for msg in st.session_state.messages:
    avatar = "🧠" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        
        # Display source citations if available
        if msg.get("sources"):
            with st.expander(f"📚 Sources ({len(msg['sources'])} chunks)", expanded=False):
                for idx, src in enumerate(msg["sources"], 1):
                    source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                    score = src.get("score", 0.0)
                    chunk_idx = src.get("chunk_index", 0)
                    st.markdown(f"**#{idx}** `{source_name}` (Chunk {chunk_idx} • Score: `{score:.4f}`)")
                    st.info(src.get("content", ""))

# Chat Input Box (Fixed to bottom on mobile)
prompt = st.chat_input("Type your question here...")

if prompt:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Query Knowledge Base
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Searching vectors..."):
            try:
                top_k_val = st.session_state.get("top_k", 4)
                res = requests.post(
                    f"{API_HOST}/search",
                    json={"query": prompt, "top_k": top_k_val},
                    timeout=30
                )
                
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    
                    if not results:
                        response_text = (
                            "🔍 No matching documents found for this question.\n\n"
                            "Tap **📤 Upload & Manage Documents** above to add files!"
                        )
                        retrieved_sources = []
                    else:
                        top_sources_text = "\n\n".join([f"- **{os.path.basename(r['source_id'])}**: \"{r['content'][:200]}...\"" for r in results[:3]])
                        response_text = (
                            f"{results[0]['content']}\n\n"
                            f"**Sources Found:**\n{top_sources_text}"
                        )
                        retrieved_sources = results
                        
                    st.markdown(response_text)
                    
                    if retrieved_sources:
                        with st.expander(f"📚 Sources ({len(retrieved_sources)} chunks)", expanded=False):
                            for idx, src in enumerate(retrieved_sources, 1):
                                source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                                score = src.get("score", 0.0)
                                chunk_idx = src.get("chunk_index", 0)
                                st.markdown(f"**#{idx}** `{source_name}` (Chunk {chunk_idx} • Score: `{score:.4f}`)")
                                st.info(src.get("content", ""))
                                
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "sources": retrieved_sources
                    })
                    
                else:
                    err_msg = f"⚠️ Server Error ({res.status_code})"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                    
            except requests.exceptions.ConnectionError:
                err_msg = "⚠️ Cannot connect to backend server. Ensure `python main.py` is running."
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
            except Exception as e:
                err_msg = f"⚠️ Error: {str(e)}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
