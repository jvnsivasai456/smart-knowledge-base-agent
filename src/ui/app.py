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
    initial_sidebar_state="collapsed"
)

# Native & Mobile PWA App Headers
st.markdown(f"""
<head>
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

/* Clean layout & max-width container */
.block-container {{
  padding-top: 1rem !important;
  padding-bottom: 5.5rem !important;
  padding-left: 0.85rem !important;
  padding-right: 0.85rem !important;
  max-width: 950px !important;
  margin: 0 auto !important;
}}

/* Native app buttons */
button {{
  min-height: 42px !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
}}

/* Tab bar modern styling */
[data-baseweb="tab-list"] {{
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  padding: 4px;
  gap: 6px;
  margin-bottom: 1rem;
}}

[data-baseweb="tab"] {{
  border-radius: 10px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.95rem;
  border: none !important;
}}

/* Chat bubbles */
[data-testid="stChatMessage"] {{
  border-radius: 16px !important;
  padding: 0.85rem 1.1rem !important;
  margin-bottom: 0.85rem !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}}

/* Card containers */
.source-card {{
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px 14px;
  margin-top: 8px;
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

# App Header
col_header, col_status = st.columns([4, 1])
with col_header:
    st.markdown("## 🧠 Smart Knowledge Base")
with col_status:
    if api_healthy:
        st.markdown("<div style='text-align:right;padding-top:12px;'><span style='background:#10B98122;color:#10B981;border:1px solid #10B98144;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;'>🟢 Online</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:right;padding-top:12px;'><span style='background:#EF444422;color:#EF4444;border:1px solid #EF444444;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;'>🔴 Offline</span></div>", unsafe_allow_html=True)

# Inside Format: Three Clean Modern Navigation Tabs
tab_chat, tab_docs, tab_settings = st.tabs(["💬 Chat Assistant", "📁 Document Library", "⚙️ Settings & Mobile"])

# ----------------------------------------------------
# TAB 1: CONVERSATIONAL CHAT ASSISTANT
# ----------------------------------------------------
with tab_chat:
    # Quick starter query buttons
    col_q1, col_q2, col_q3 = st.columns(3)
    sample_q = None
    with col_q1:
        if st.button("📌 Summarize docs", use_container_width=True):
            sample_q = "Summarize the key topics and contents in the uploaded documents."
    with col_q2:
        if st.button("🔍 Key takeaways", use_container_width=True):
            sample_q = "What are the most important key takeaways from the documents?"
    with col_q3:
        if st.button("❓ Main concepts", use_container_width=True):
            sample_q = "Explain the core concepts and definitions found in the documents."

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 **Hello!** I am your **Knowledge Base Assistant**.\n\nAsk me any question about your documents, or tap **📁 Document Library** above to upload new files!",
                "sources": []
            }
        ]

    # Display Previous Messages
    for msg in st.session_state.messages:
        avatar = "🧠" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
            # Display source citations if available
            if msg.get("sources"):
                with st.expander(f"📚 Verified Sources ({len(msg['sources'])} chunks)", expanded=False):
                    for idx, src in enumerate(msg["sources"], 1):
                        source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                        score = src.get("score", 0.0)
                        chunk_idx = src.get("chunk_index", 0)
                        
                        # Calculate intuitive similarity score
                        match_pct = max(10, min(99, int((1.0 - (score / 2.0)) * 100)))
                        
                        st.markdown(f"**Source #{idx}:** `{source_name}` &nbsp;•&nbsp; **Chunk {chunk_idx}** &nbsp;•&nbsp; <span style='color:#10B981;font-weight:600;'>{match_pct}% Match</span>", unsafe_allow_html=True)
                        st.info(src.get("content", ""))

    # Chat Input Box
    prompt = st.chat_input("Ask a question about your documents...")
    if sample_q:
        prompt = sample_q

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Searching semantic knowledge base in ChromaDB..."):
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
                                "🔍 **No matching information found.**\n\n"
                                "I searched the knowledge base but couldn't find relevant content. "
                                "Go to the **📁 Document Library** tab to upload relevant documents!"
                            )
                            retrieved_sources = []
                        else:
                            # Clean, polished answer synthesized from top matching context
                            top_content = results[0]['content'].strip()
                            
                            # Construct source badge list
                            source_pills = " ".join([f"`📄 {os.path.basename(r['source_id'])}`" for r in results[:3]])
                            
                            response_text = f"{top_content}\n\n---\n**Grounded in:** {source_pills}"
                            retrieved_sources = results
                            
                        st.markdown(response_text)
                        
                        if retrieved_sources:
                            with st.expander(f"📚 Verified Sources ({len(retrieved_sources)} chunks)", expanded=False):
                                for idx, src in enumerate(retrieved_sources, 1):
                                    source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                                    score = src.get("score", 0.0)
                                    chunk_idx = src.get("chunk_index", 0)
                                    match_pct = max(10, min(99, int((1.0 - (score / 2.0)) * 100)))
                                    st.markdown(f"**Source #{idx}:** `{source_name}` &nbsp;•&nbsp; **Chunk {chunk_idx}** &nbsp;•&nbsp; <span style='color:#10B981;font-weight:600;'>{match_pct}% Match</span>", unsafe_allow_html=True)
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
                    err_msg = "⚠️ Cannot connect to backend server. Ensure `python main.py` is running on port 8000."
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                except Exception as e:
                    err_msg = f"⚠️ Error: {str(e)}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

# ----------------------------------------------------
# TAB 2: DOCUMENT LIBRARY & UPLOAD ZONE
# ----------------------------------------------------
with tab_docs:
    st.subheader("📤 Ingest New Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF, Word (DOCX), or Text (TXT) files:",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="doc_library_uploader"
    )
    
    if st.button("⚡ Ingest & Re-index", use_container_width=True):
        if uploaded_files and api_healthy:
            success_count = 0
            for uf in uploaded_files:
                with st.spinner(f"Ingesting {uf.name}..."):
                    files = {"file": (uf.name, uf.getvalue())}
                    try:
                        res = requests.post(f"{API_HOST}/upload", files=files, timeout=30)
                        if res.status_code == 200:
                            success_count += 1
                    except Exception as e:
                        st.error(f"Error uploading {uf.name}: {e}")
            if success_count > 0:
                st.success(f"✅ Successfully ingested {success_count} file(s) into ChromaDB!")
        elif not uploaded_files:
            st.warning("Please choose one or more files to upload.")
        else:
            st.error("Backend API is offline.")

    st.divider()
    st.subheader("📚 Currently Indexed Files")
    
    # Fetch indexed documents list from API
    try:
        doc_res = requests.get(f"{API_HOST}/documents", timeout=5)
        if doc_res.status_code == 200:
            docs = doc_res.json().get("documents", [])
            if not docs:
                st.info("No documents indexed yet. Upload your first document above!")
            else:
                for d in docs:
                    filename = os.path.basename(d.get("source_id", "Unknown"))
                    file_type = d.get("source_type", "txt").upper()
                    icon = "📕" if file_type == "PDF" else "📘" if file_type == "DOCX" else "📄"
                    last_indexed = d.get("last_indexed", "Recently")[:19].replace("T", " ")
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="source-card">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                              <strong style="font-size:15px;">{icon} {filename}</strong><br>
                              <span style="font-size:12px;color:#9CA3AF;">Type: {file_type} &nbsp;•&nbsp; Indexed: {last_indexed}</span>
                            </div>
                            <span style="background:#4F46E522;color:#818CF8;border:1px solid #4F46E544;padding:3px 8px;border-radius:6px;font-size:11px;font-family:monospace;">Active in ChromaDB</span>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
    except Exception:
        st.warning("Could not retrieve file library from server.")

# ----------------------------------------------------
# TAB 3: SETTINGS, CONTROLS & MOBILE APP
# ----------------------------------------------------
with tab_settings:
    st.subheader("⚙️ Retrieval Parameters")
    st.session_state["top_k"] = st.slider("Number of source chunks to retrieve (Top-K):", min_value=1, max_value=8, value=4)
    
    st.divider()
    st.subheader("🧹 Chat Management")
    if st.button("🗑️ Reset All Chat History", use_container_width=True):
        st.session_state.messages = []
        st.success("Chat history cleared!")
        st.rerun()

    st.divider()
    st.subheader("📱 Install & Open on Mobile")
    st.markdown("Scan this QR code with your phone camera to open and install the app on your mobile home screen:")
    
    qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mobile_qr.png")
    if os.path.exists(qr_path):
        st.image(qr_path, width=220)
    st.code("http://192.168.1.53:8501", language="text")
    st.caption("Ensure both phone and computer are on the same Wi-Fi network.")
