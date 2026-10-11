import streamlit as st
import requests
import os

# API Host configuration
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Smart KB Chatbot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Native App Clean Styling (removes website headers, toolbars, deploy buttons)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="stDecoration"] {display: none;}
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

# Sidebar for Document Management
with st.sidebar:
    st.header("📁 Document Ingestion")
    
    # Server status badge
    if api_healthy:
        st.success("🟢 Backend API Connected", icon="✅")
    else:
        st.error("🔴 Backend API Disconnected (Check main.py)", icon="⚠️")
        
    uploaded_file = st.file_uploader(
        "Upload new document (PDF, DOCX, TXT):",
        type=["pdf", "docx", "txt"]
    )
    
    if st.button("📤 Upload & Ingest", use_container_width=True):
        if uploaded_file and api_healthy:
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    res = requests.post(f"{API_HOST}/upload", files=files, timeout=30)
                    if res.status_code == 200:
                        st.success(f"✅ Ingested **{uploaded_file.name}**! Auto-chunked & indexed into ChromaDB.")
                    else:
                        st.error(f"Failed: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        elif not uploaded_file:
            st.warning("Please choose a file first.")
        else:
            st.error("Cannot upload: Backend API is not reachable.")

    st.divider()
    
    # Chat controls
    st.subheader("⚙️ Chat Settings")
    bot_icon_choice = st.selectbox(
        "Chatbot Icon / Avatar:",
        ["🧠 Brain (Neural)", "⚡ Lightning", "🤖 Robot", "✨ Sparkles", "📚 Knowledge Base", "🔮 Oracle"],
        index=0
    )
    bot_icon = bot_icon_choice.split()[0]
    top_k = st.slider("Max source chunks to retrieve:", min_value=1, max_value=10, value=4)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Custom header styling
st.title(f"{bot_icon} Smart Knowledge Base Chatbot")
st.caption("Ask questions and get answers grounded in your uploaded documents via vector search.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hello! I am your **Smart Knowledge Base Assistant**.\n\nUpload your documents in the sidebar, or ask me any question about your indexed knowledge base!",
            "sources": []
        }
    ]

# Display Previous Messages
for msg in st.session_state.messages:
    msg_avatar = bot_icon if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=msg_avatar):
        st.markdown(msg["content"])
        
        # Display source citations if available
        if msg.get("sources"):
            with st.expander(f"📚 View Retrieved Sources ({len(msg['sources'])} chunks)", expanded=False):
                for idx, src in enumerate(msg["sources"], 1):
                    source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                    score = src.get("score", 0.0)
                    chunk_idx = src.get("chunk_index", 0)
                    
                    st.markdown(f"**Source {idx}:** `{source_name}` (Chunk #{chunk_idx} • L2 Distance: `{score:.4f}`)")
                    st.info(src.get("content", ""))

# Chat Input & Response Handling
prompt = st.chat_input("Ask a question about your documents...")

if prompt:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Query Knowledge Base & Generate Answer
    with st.chat_message("assistant", avatar=bot_icon):
        with st.spinner("Searching semantic embeddings in ChromaDB..."):
            try:
                res = requests.post(
                    f"{API_HOST}/search",
                    json={"query": prompt, "top_k": top_k},
                    timeout=30
                )
                
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    
                    if not results:
                        response_text = (
                            "🔍 I searched your knowledge base, but couldn't find any documents closely matching your query.\n\n"
                            "Try uploading a relevant document in the sidebar, or rephrasing your question!"
                        )
                        retrieved_sources = []
                    else:
                        # Synthesize answers grounded in the retrieved chunks
                        top_sources_text = "\n\n".join([f"- **{os.path.basename(r['source_id'])}**: \"{r['content'][:250]}...\"" for r in results[:3]])
                        
                        response_text = (
                            f"Based on your knowledge base, here is the most relevant information:\n\n"
                            f"> {results[0]['content']}\n\n"
                            f"**Key matching documents:**\n{top_sources_text}"
                        )
                        retrieved_sources = results
                        
                    st.markdown(response_text)
                    
                    if retrieved_sources:
                        with st.expander(f"📚 View Retrieved Sources ({len(retrieved_sources)} chunks)", expanded=False):
                            for idx, src in enumerate(retrieved_sources, 1):
                                source_name = os.path.basename(src.get("source_id", "Unknown Document"))
                                score = src.get("score", 0.0)
                                chunk_idx = src.get("chunk_index", 0)
                                st.markdown(f"**Source {idx}:** `{source_name}` (Chunk #{chunk_idx} • Distance: `{score:.4f}`)")
                                st.info(src.get("content", ""))
                                
                    # Save to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "sources": retrieved_sources
                    })
                    
                else:
                    err_msg = f"⚠️ API Error ({res.status_code}): {res.text}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})
                    
            except requests.exceptions.ConnectionError:
                err_msg = "⚠️ Could not connect to FastAPI backend. Ensure `python main.py` is running on port 8000."
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
            except Exception as e:
                err_msg = f"⚠️ An unexpected error occurred: {str(e)}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
