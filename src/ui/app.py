import streamlit as st
import requests
import os
import time
import json
import base64
import urllib.parse

# Backend configuration
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")

# Mobile PWA Manifest
pwa_manifest = {
    "name": "Smart Knowledge Base",
    "short_name": "SmartKB",
    "description": "Next-Gen AI Semantic Knowledge Base Assistant",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0B0F19",
    "theme_color": "#6366F1",
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
    page_title="Smart Knowledge Base",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Clean Styling
clean_css = """<style>
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden;
    display: none !important;
}
html, body, [class*="css"] {
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 6rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 960px !important;
    margin: 0 auto !important;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818CF8 0%, #C084FC 50%, #38BDF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.hero-subtitle {
    font-size: 0.88rem;
    color: #94A3B8;
    margin-bottom: 1.2rem;
}
.status-badge-online {
    background: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.25);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.status-badge-offline {
    background: rgba(239, 68, 68, 0.12);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.25);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
[data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 6px;
    gap: 8px;
    margin-bottom: 1.4rem;
    backdrop-filter: blur(12px);
}
[data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    border: none !important;
    color: #94A3B8 !important;
    transition: all 0.2s ease !important;
}
[aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.25) 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(168, 85, 247, 0.4) !important;
}
[data-testid="stChatMessage"] {
    border-radius: 18px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 1rem !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    background: rgba(255, 255, 255, 0.02) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}
[data-testid="stBottomBlockContainer"] {
    background: rgba(11, 15, 25, 0.88) !important;
    backdrop-filter: blur(16px) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-bottom: env(safe-area-inset-bottom, 1rem) !important;
}
.doc-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.15s ease;
}
.doc-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
}
button {
    min-height: 42px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
@media (max-width: 768px) {
    .hero-title { font-size: 1.45rem; }
    .hero-subtitle { font-size: 0.8rem; }
    .block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; }
}
</style>"""
st.markdown(clean_css, unsafe_allow_html=True)

# ----------------------------------------------------
# BACKEND HEALTH & STATS CHECK
# ----------------------------------------------------
api_healthy = False
latency_ms = 0
try:
    t0 = time.time()
    health_resp = requests.get(f"{API_HOST}/health", timeout=2)
    latency_ms = int((time.time() - t0) * 1000)
    if health_resp.status_code == 200:
        api_healthy = True
except Exception:
    api_healthy = False

# Fetch currently indexed documents
indexed_docs = []
if api_healthy:
    try:
        doc_resp = requests.get(f"{API_HOST}/documents", timeout=3)
        if doc_resp.status_code == 200:
            indexed_docs = doc_resp.json().get("documents", [])
    except Exception:
        pass

# ----------------------------------------------------
# TOP HEADER & CONTROL DASHBOARD
# ----------------------------------------------------
col_title, col_stat = st.columns([3, 1.2])

with col_title:
    st.markdown('<div class="hero-title">🧠 Smart Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Semantic Search • Multi-Format Ingestion • Vector RAG Engine</div>', unsafe_allow_html=True)

with col_stat:
    if api_healthy:
        st.markdown(
            f"""<div style="text-align: right; padding-top: 6px;">
            <span class="status-badge-online">● Active &bull; {latency_ms}ms</span>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">{len(indexed_docs)} documents indexed</div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """<div style="text-align: right; padding-top: 6px;">
            <span class="status-badge-offline">● Backend Offline</span>
            <div style="font-size: 11px; color: #EF4444; margin-top: 4px;">Start backend: `python main.py`</div>
            </div>""",
            unsafe_allow_html=True
        )

# ----------------------------------------------------
# THREE NAVIGATION TABS
# ----------------------------------------------------
tab_chat, tab_library, tab_controls = st.tabs([
    "💬 AI Chat Assistant",
    f"📁 Knowledge Library ({len(indexed_docs)})",
    "🎛️ Controls & Mobile"
])

# ====================================================
# TAB 1: AI CHAT ASSISTANT
# ====================================================
with tab_chat:
    # Quick Starter Prompt Chips
    col_chip1, col_chip2, col_chip3 = st.columns(3)
    quick_prompt = None

    with col_chip1:
        if st.button("📋 Summarize Documents", use_container_width=True):
            quick_prompt = "Provide a comprehensive summary of the main points across the uploaded documents."
    with col_chip2:
        if st.button("🔍 Key Takeaways", use_container_width=True):
            quick_prompt = "What are the most critical takeaways, findings, and conclusions?"
    with col_chip3:
        if st.button("💡 Core Concepts", use_container_width=True):
            quick_prompt = "Identify and clearly explain the core concepts and definitions mentioned."

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Hello! I'm your Smart Knowledge Base Assistant.**\n\n"
                    "I have ingested your documents into ChromaDB vector embeddings. "
                    "Ask me any question, or click one of the quick starter buttons above to explore!"
                ),
                "sources": []
            }
        ]

    # Render Conversation Messages
    for msg in st.session_state.messages:
        avatar = "🧠" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
            # Source Citations Card
            if msg.get("sources"):
                with st.expander(f"📚 Verified Sources ({len(msg['sources'])} relevant chunks)", expanded=False):
                    for idx, src in enumerate(msg["sources"], 1):
                        source_file = os.path.basename(src.get("source_id", "Document"))
                        score = src.get("score", 0.0)
                        chunk_idx = src.get("chunk_index", 0)
                        
                        match_pct = max(15, min(99, int((1.0 - (score / 2.0)) * 100)))
                        badge_color = "#34D399" if match_pct >= 80 else "#818CF8"
                        
                        st.markdown(
                            f"""<div style="margin-bottom: 6px;">
                            <strong>#{idx}</strong> <code>{source_file}</code> &bull; Chunk {chunk_idx} &bull; 
                            <span style="color: {badge_color}; font-weight: 700;">{match_pct}% Match</span>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        st.info(src.get("content", ""))

    # Chat Input Box
    user_input = st.chat_input("Ask anything about your documents...")
    active_prompt = quick_prompt if quick_prompt else user_input

    if active_prompt:
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_prompt)

        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Synthesizing answer from semantic knowledge base..."):
                try:
                    search_depth = st.session_state.get("top_k", 4)
                    # Call smart /chat endpoint
                    chat_res = requests.post(
                        f"{API_HOST}/chat",
                        json={"query": active_prompt, "top_k": search_depth},
                        timeout=30
                    )
                    
                    if chat_res.status_code == 200:
                        data = chat_res.json()
                        answer_text = data.get("answer", "")
                        sources = data.get("sources", [])
                        
                        st.markdown(answer_text)
                        
                        if sources:
                            with st.expander(f"📚 Verified Sources ({len(sources)} relevant chunks)", expanded=False):
                                for idx, src in enumerate(sources, 1):
                                    source_file = os.path.basename(src.get("source_id", "Document"))
                                    score = src.get("score", 0.0)
                                    chunk_idx = src.get("chunk_index", 0)
                                    match_pct = max(15, min(99, int((1.0 - (score / 2.0)) * 100)))
                                    badge_color = "#34D399" if match_pct >= 80 else "#818CF8"
                                    
                                    st.markdown(
                                        f"""<div style="margin-bottom: 6px;">
                                        <strong>#{idx}</strong> <code>{source_file}</code> &bull; Chunk {chunk_idx} &bull; 
                                        <span style="color: {badge_color}; font-weight: 700;">{match_pct}% Match</span>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                                    st.info(src.get("content", ""))
                                    
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer_text,
                            "sources": sources
                        })
                    else:
                        err = f"⚠️ Server Error ({chat_res.status_code}): {chat_res.text}"
                        st.error(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})
                        
                except requests.exceptions.ConnectionError:
                    err = "⚠️ Backend API is offline. Please start the backend with `python main.py` on port 8000."
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})
                except Exception as e:
                    err = f"⚠️ Error: {str(e)}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})

# ====================================================
# TAB 2: KNOWLEDGE LIBRARY & DOCUMENT INGESTION
# ====================================================
with tab_library:
    st.subheader("📤 Document Ingestion Dropzone")
    st.caption("Upload files to automatically extract text, generate 384-d vector embeddings, and index them in ChromaDB.")
    
    new_files = st.file_uploader(
        "Drop PDF, DOCX, or TXT files here:",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="uploader_widget"
    )
    
    col_upload_btn, col_resync_btn = st.columns([2, 1])
    with col_upload_btn:
        if st.button("🚀 Ingest & Index Uploaded Files", use_container_width=True, type="primary"):
            if new_files and api_healthy:
                successes = 0
                for f in new_files:
                    with st.spinner(f"Ingesting {f.name}..."):
                        files_payload = {"file": (f.name, f.getvalue())}
                        try:
                            r = requests.post(f"{API_HOST}/upload", files=files_payload, timeout=30)
                            if r.status_code == 200:
                                successes += 1
                        except Exception as e:
                            st.error(f"Error indexing {f.name}: {e}")
                if successes > 0:
                    st.success(f"✅ Ingested {successes} document(s)! Embeddings saved in ChromaDB.")
                    time.sleep(1)
                    st.rerun()
            elif not new_files:
                st.warning("Please select at least one file to upload.")
            else:
                st.error("Backend API is currently offline.")
                
    with col_resync_btn:
        if st.button("🔄 Resync & Refresh Library", use_container_width=True):
            if api_healthy:
                try:
                    requests.post(f"{API_HOST}/resync", timeout=5)
                except Exception:
                    pass
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.subheader(f"📚 Currently Indexed Corpus ({len(indexed_docs)} documents)")

    if not indexed_docs:
        st.info("No documents indexed yet. Drag and drop your first file above to get started!")
    else:
        for doc in indexed_docs:
            src_path = doc.get("source_id", "Unknown")
            fname = doc.get("filename") or os.path.basename(src_path)
            ftype = doc.get("source_type", "txt").upper()
            icon = "📕" if ftype == "PDF" else "📘" if ftype == "DOCX" else "📄"
            fhash = doc.get("file_hash", "")[:12]
            indexed_at = doc.get("last_indexed", "Recently")[:19].replace("T", " ")
            size_bytes = doc.get("file_size_bytes", 0)
            
            size_str = ""
            if size_bytes > 0:
                if size_bytes < 1024:
                    size_str = f"&bull; Size: <strong>{size_bytes} B</strong>"
                elif size_bytes < 1024 * 1024:
                    size_str = f"&bull; Size: <strong>{size_bytes/1024:.1f} KB</strong>"
                else:
                    size_str = f"&bull; Size: <strong>{size_bytes/(1024*1024):.1f} MB</strong>"
            
            col_card, col_del = st.columns([5, 1.2])
            with col_card:
                st.markdown(
                    f"""<div class="doc-card" style="margin-bottom: 0px;">
                      <div>
                        <div style="font-weight: 700; font-size: 0.98rem; display: flex; align-items: center; gap: 8px;">
                          <span>{icon}</span> {fname}
                        </div>
                        <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">
                          Format: <strong>{ftype}</strong> {size_str} &bull; SHA-256: <code>{fhash}...</code> &bull; Indexed: {indexed_at}
                        </div>
                      </div>
                      <div>
                        <span style="background: rgba(99, 102, 241, 0.15); color: #818CF8; border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 10px; border-radius: 8px; font-size: 0.74rem; font-weight: 600;">
                          ChromaDB Active
                        </span>
                      </div>
                    </div>""",
                    unsafe_allow_html=True
                )
            with col_del:
                st.write("")
                if st.button("🗑️ Delete", key=f"del_{fname}", use_container_width=True):
                    try:
                        encoded_fname = urllib.parse.quote(fname)
                        del_res = requests.delete(f"{API_HOST}/documents/{encoded_fname}", timeout=10)
                        if del_res.status_code == 200:
                            st.toast(f"Deleted {fname}", icon="🗑️")
                            st.success(f"Successfully deleted {fname}")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {del_res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            st.write("")

# ====================================================
# TAB 3: APP CONTROLS, SETTINGS & MOBILE
# ====================================================
with tab_controls:
    st.subheader("🎛️ Search Precision & Retrieval Depth")
    st.session_state["top_k"] = st.slider(
        "Top-K Chunks to Retrieve per Query:",
        min_value=1,
        max_value=8,
        value=st.session_state.get("top_k", 4),
        help="Controls the number of semantic vector chunks retrieved from ChromaDB for each query."
    )
    
    st.markdown("---")
    st.subheader("🧹 Chat Session Controls")
    if st.button("🗑️ Clear Conversation History", use_container_width=True):
        st.session_state.messages = []
        st.success("Chat history cleared!")
        time.sleep(0.5)
        st.rerun()

    st.markdown("---")
    st.subheader("📱 Install on Mobile Device")
    st.caption("Scan this QR code with your iPhone or Android camera to open and install the app on your home screen:")
    
    col_qr, col_qr_info = st.columns([1, 2])
    with col_qr:
        qr_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mobile_qr.png")
        if os.path.exists(qr_file):
            st.image(qr_file, width=180)
    with col_qr_info:
        st.markdown("**Mobile Network Link:**")
        st.code("http://192.168.1.53:8501", language="text")
        st.caption("Ensure your phone is connected to the same Wi-Fi network.")
        st.markdown("""
        * **iPhone (Safari)**: Tap Share ➔ *Add to Home Screen*.
        * **Android (Chrome)**: Tap Menu (⋮) ➔ *Install app* or *Add to Home screen*.
        """)

    st.markdown("---")
    st.subheader("🔌 System Diagnostics")
    st.markdown(f"- **FastAPI Backend:** `{API_HOST}` ({'Online 🟢' if api_healthy else 'Offline 🔴'})")
    st.markdown(f"- **Embedding Model:** `all-MiniLM-L6-v2` (SentenceTransformers 384-d)")
    if api_healthy:
        st.markdown(f"- **API Latency:** `{latency_ms} ms`")
        st.markdown(f"- **Indexed Documents:** `{len(indexed_docs)}`")
    st.markdown(f"- **Vector Database:** `ChromaDB Persistent (data/chroma_db)`")
    st.markdown(f"- **Metadata Database:** `SQLite (data/metadata.sqlite)`")
