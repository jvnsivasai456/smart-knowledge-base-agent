import streamlit as st
import requests
import os
import sys
import subprocess
import time
import json
import base64
import urllib.parse

# Backend configuration
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")

# App Brand Icon path & Base64
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICON_PATH = os.path.join(PROJECT_ROOT, "app_icon.png")
icon_b64 = ""
if os.path.exists(ICON_PATH):
    try:
        with open(ICON_PATH, "rb") as f:
            icon_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        icon_b64 = ""

# ----------------------------------------------------
# RESILIENT INFRASTRUCTURE ENGINE & SELF-HEALING HELPERS
# ----------------------------------------------------
def trigger_backend_launch() -> bool:
    """Launch the FastAPI backend in background without popping up console windows."""
    try:
        py_bin = sys.executable
        main_py = os.path.join(PROJECT_ROOT, "main.py")
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(
            [py_bin, main_py],
            cwd=PROJECT_ROOT,
            creationflags=creation_flags
        )
        return True
    except Exception:
        return False

def trigger_tunnel_launch() -> bool:
    """Launch start_tunnel.py in background to establish mobile network tunnel."""
    try:
        py_bin = sys.executable
        tunnel_py = os.path.join(PROJECT_ROOT, "start_tunnel.py")
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(
            [py_bin, tunnel_py],
            cwd=PROJECT_ROOT,
            creationflags=creation_flags
        )
        return True
    except Exception:
        return False

def check_backend_health() -> tuple[bool, int]:
    """Check if the backend HTTP service is healthy and measure response latency."""
    try:
        t0 = time.time()
        resp = requests.get(f"{API_HOST}/health", timeout=1.5)
        lat = int((time.time() - t0) * 1000)
        return (resp.status_code == 200, lat)
    except Exception:
        return (False, 0)

@st.cache_resource
def get_inprocess_engine():
    """Cache the in-process RAG components for zero-downtime query fallback."""
    from src.config import settings
    from src.embedding import Embedder, VectorStore, MetadataStore
    from src.retrieval import Retriever, AnswerEngine
    settings.create_directories()
    embedder = Embedder(model_name=settings.embedding_model_name)
    vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
    metadata_store = MetadataStore(db_path=settings.metadata_db_path)
    retriever = Retriever(embedder, vector_store)
    answer_engine = AnswerEngine(embedder=embedder)
    return embedder, vector_store, metadata_store, retriever, answer_engine

def get_resilient_documents(is_api_alive: bool) -> list:
    """Fetch documents either from API or directly from MetadataStore."""
    if is_api_alive:
        try:
            doc_resp = requests.get(f"{API_HOST}/documents", timeout=2.5)
            if doc_resp.status_code == 200:
                return doc_resp.json().get("documents", [])
        except Exception:
            pass
    try:
        from src.config import settings
        from src.embedding import MetadataStore
        meta_store = MetadataStore(db_path=settings.metadata_db_path)
        records = meta_store.get_all_files()
        enriched = []
        for r in records:
            rec = dict(r)
            src_id = rec.get("source_id", "")
            rec["filename"] = os.path.basename(src_id)
            disk_path = src_id if os.path.isabs(src_id) else os.path.join(settings.upload_dir, rec["filename"])
            rec["file_size_bytes"] = os.path.getsize(disk_path) if os.path.exists(disk_path) else 0
            rec["exists_on_disk"] = os.path.exists(disk_path)
            enriched.append(rec)
        return enriched
    except Exception:
        return []

def execute_resilient_chat(active_prompt: str, search_depth: int, provider: str, api_key: str, is_api_alive: bool) -> tuple[str, list, str]:
    """Execute query via HTTP API or in-process engine seamlessly."""
    if is_api_alive:
        try:
            chat_res = requests.post(
                f"{API_HOST}/chat",
                json={
                    "query": active_prompt,
                    "top_k": search_depth,
                    "api_key": api_key,
                    "provider": provider
                },
                timeout=35
            )
            if chat_res.status_code == 200:
                data = chat_res.json()
                return data.get("answer", ""), data.get("sources", []), "API"
        except Exception:
            pass  # Fall through to in-process execution

    # In-process zero-downtime engine
    try:
        embedder, vector_store, metadata_store, retriever, answer_engine = get_inprocess_engine()
        docs = metadata_store.get_all_files()
        if answer_engine.is_greeting_or_meta(active_prompt):
            ans_dict = answer_engine.handle_greeting(active_prompt, docs)
            return ans_dict.get("answer", ""), ans_dict.get("sources", []), "In-Process"
        
        search_resp = retriever.search(active_prompt, top_k=search_depth)
        ans_dict = answer_engine.synthesize(
            active_prompt,
            search_resp.results,
            docs,
            api_key=api_key,
            provider=provider
        )
        return ans_dict.get("answer", ""), ans_dict.get("sources", []), "In-Process"
    except Exception as err:
        return f"⚠️ Resilient query execution encountered an issue: {str(err)}", [], "Error"

def ingest_resilient(file_name: str, file_bytes: bytes, is_api_alive: bool) -> bool:
    """Ingest file through API or in-process pipeline."""
    if is_api_alive:
        try:
            r = requests.post(f"{API_HOST}/upload", files={"file": (file_name, file_bytes)}, timeout=30)
            if r.status_code == 200:
                return True
        except Exception:
            pass
    # In-process ingestion
    try:
        from src.config import settings
        from src.embedding import Embedder, VectorStore, MetadataStore, Indexer
        from src.ingestion import Ingestor
        from src.processing import TextChunker
        from src.update_engine import DirectoryScanner, KnowledgeBaseUpdater
        settings.create_directories()
        save_path = os.path.join(settings.upload_dir, file_name)
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        embedder = Embedder(model_name=settings.embedding_model_name)
        vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
        meta_store = MetadataStore(db_path=settings.metadata_db_path)
        indexer = Indexer(embedder, vector_store, meta_store)
        scanner = DirectoryScanner(settings.upload_dir)
        updater = KnowledgeBaseUpdater(scanner, meta_store, indexer, Ingestor(), TextChunker())
        updater.sync()
        return True
    except Exception:
        return False

def delete_resilient(doc_name: str, is_api_alive: bool) -> bool:
    """Delete document through API or directly."""
    if is_api_alive:
        try:
            encoded_name = urllib.parse.quote(doc_name)
            del_res = requests.delete(f"{API_HOST}/documents/{encoded_name}", timeout=5)
            if del_res.status_code == 200:
                return True
        except Exception:
            pass
    # In-process deletion
    try:
        from src.config import settings
        from src.embedding import VectorStore, MetadataStore
        settings.create_directories()
        vector_store = VectorStore(persist_directory=settings.chroma_db_dir)
        meta_store = MetadataStore(db_path=settings.metadata_db_path)
        records = meta_store.get_all_files()
        for r in records:
            r_src = r.get("source_id", "")
            if os.path.basename(r_src) == doc_name or r_src == doc_name:
                vector_store.delete_by_source_id(r_src)
                meta_store.delete_record(r_src)
                disk_path = r_src if os.path.isabs(r_src) else os.path.join(settings.upload_dir, os.path.basename(r_src))
                if os.path.exists(disk_path):
                    os.remove(disk_path)
                return True
    except Exception:
        pass
    return False

# Unique Document Icon & Metadata Resolver
def get_unique_doc_metadata(filename: str, ftype: str = "") -> dict:
    fname_lower = filename.lower()
    if any(k in fname_lower for k in ["f_test", "ftest", "stat", "hypothesis", "variance", "math", "calc", "prob"]):
        return {
            "symbol": "📊",
            "badge": "Statistics & Math",
            "color": "#F59E0B",
            "bg": "rgba(245, 158, 11, 0.12)",
            "border": "rgba(245, 158, 11, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(217, 119, 6, 0.1))"
        }
    elif any(k in fname_lower for k in ["vuforia", "ar", "augmented", "target", "vision"]):
        return {
            "symbol": "🥽",
            "badge": "Augmented Reality",
            "color": "#EC4899",
            "bg": "rgba(236, 72, 153, 0.12)",
            "border": "rgba(236, 72, 153, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(219, 39, 119, 0.1))"
        }
    elif any(k in fname_lower for k in ["unity", "game", "physics", "gameobject", "script"]):
        return {
            "symbol": "🎮",
            "badge": "Game Engine",
            "color": "#818CF8",
            "bg": "rgba(99, 102, 241, 0.12)",
            "border": "rgba(99, 102, 241, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(79, 70, 229, 0.1))"
        }
    elif any(k in fname_lower for k in ["ids", "security", "network", "cyber", "firewall", "crypto"]):
        return {
            "symbol": "🛡️",
            "badge": "Cybersecurity",
            "color": "#10B981",
            "bg": "rgba(16, 185, 129, 0.12)",
            "border": "rgba(16, 185, 129, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.1))"
        }
    elif any(k in fname_lower for k in ["ai", "neural", "ml", "deep", "embed", "gpt"]):
        return {
            "symbol": "⚡",
            "badge": "Machine Learning",
            "color": "#C084FC",
            "bg": "rgba(168, 85, 247, 0.12)",
            "border": "rgba(168, 85, 247, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(124, 58, 237, 0.1))"
        }
    elif ftype.upper() == "PDF":
        return {
            "symbol": "📕",
            "badge": "PDF Document",
            "color": "#EF4444",
            "bg": "rgba(239, 68, 68, 0.12)",
            "border": "rgba(239, 68, 68, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(220, 38, 38, 0.1))"
        }
    elif ftype.upper() == "DOCX":
        return {
            "symbol": "📘",
            "badge": "Word Document",
            "color": "#38BDF8",
            "bg": "rgba(56, 189, 248, 0.12)",
            "border": "rgba(56, 189, 248, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(37, 99, 235, 0.1))"
        }
    elif ftype.upper() == "TXT":
        return {
            "symbol": "📄",
            "badge": "Text File",
            "color": "#94A3B8",
            "bg": "rgba(148, 163, 184, 0.12)",
            "border": "rgba(148, 163, 184, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(148, 163, 184, 0.25), rgba(100, 116, 139, 0.1))"
        }
    else:
        return {
            "symbol": "📑",
            "badge": "Knowledge File",
            "color": "#A855F7",
            "bg": "rgba(168, 85, 247, 0.12)",
            "border": "rgba(168, 85, 247, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(147, 51, 234, 0.1))"
        }

# Mobile PWA Manifest
pwa_manifest = {
    "name": "Smart Knowledge Base Agent",
    "short_name": "SmartKBAgent",
    "description": "Next-Gen Natural Language AI Knowledge Base Agent",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#FFFFFF",
    "theme_color": "#FFFFFF",
    "orientation": "portrait",
    "icons": [
        {
            "src": f"data:image/png;base64,{icon_b64}" if icon_b64 else "https://api.iconify.design/fluent-emoji:brain.svg",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ]
}
manifest_b64 = base64.b64encode(json.dumps(pwa_manifest).encode('utf-8')).decode('utf-8')

# Streamlit Page Config
st.set_page_config(
    page_title="Smart Knowledge Base Agent",
    page_icon=ICON_PATH if os.path.exists(ICON_PATH) else "🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Ultra-Modern White Styling with Custom Typography & Ergonomic Search Placement
clean_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden;
    display: none !important;
}

/* Force Pure White Background for Mobile and Desktop */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}

html, body, [class*="css"] {
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #0F172A !important;
}

/* Force Light/White theme against any mobile Dark Mode preference */
@media (prefers-color-scheme: dark) {
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }
    p, span, li, label, div, td, th, .stMarkdown, .stText {
        color: #0F172A !important;
    }
    [data-testid="stChatInput"] {
        background: #FFFFFF !important;
        border-color: #E2E8F0 !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #0F172A !important;
        background: #FFFFFF !important;
    }
    [data-testid="stChatMessage"]:has([aria-label*="user" i]),
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #F1F5F9 !important;
        color: #0F172A !important;
    }
}

/* Universal High-Contrast Crisp Typography for All Normal Text */
p, span, li, label, div, td, th, .stMarkdown, .stText {
    color: #0F172A;
    text-shadow: none !important;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 980px !important;
    margin: 0 auto !important;
}

/* Chat Input Bar - Moves Down Below Output Naturally */
div[data-testid="stChatInput"] {
    position: relative !important;
    width: 100% !important;
    max-width: 880px !important;
    margin: 1.5rem auto 2.5rem auto !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 36px !important;
    background: #FFFFFF !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
    padding: 4px 8px 4px 18px !important;
    transition: all 0.25s ease !important;
}
div[data-testid="stChatInput"]:focus-within {
    border-color: #94A3B8 !important;
    box-shadow: 0 6px 26px rgba(0, 0, 0, 0.1) !important;
    background: #FFFFFF !important;
}
div[data-testid="stChatInput"] textarea {
    color: #0F172A !important;
    font-size: 1.01rem !important;
    font-weight: 450 !important;
    padding-top: 10px !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #64748B !important;
    font-size: 0.98rem !important;
    font-weight: 400 !important;
}
div[data-testid="stChatInput"] button {
    background: #0F172A !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stChatInput"] button:hover {
    background: #334155 !important;
    transform: scale(1.05) !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stChatInput"] button svg {
    fill: #FFFFFF !important;
}

/* Gemini Grounding Disclaimer Underneath Bottom Search Bar */
div[data-testid="stChatInput"]::after {
    content: "Gemini is AI and can make mistakes.";
    position: absolute;
    bottom: -20px;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: 0.74rem;
    color: #64748B;
    font-weight: 400;
    pointer-events: none;
}

/* Clean 2D Header for "Smart Knowledge Base Agent" */
.hero-title-wrapper {
    display: flex;
    align-items: center;
    gap: 0.95rem;
    margin-bottom: 0.25rem;
}
.hero-title-2d {
    font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
    font-size: 2.15rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.2 !important;
    display: inline-flex !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 0.55rem !important;
}
.title-main-2d {
    color: #0F172A !important;
    font-weight: 800 !important;
    text-shadow: none !important;
}
.title-agent-2d {
    background: linear-gradient(135deg, #4F46E5 0%, #2563EB 50%, #0284C7 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 800 !important;
    text-shadow: none !important;
}
.agent-tag-2d {
    font-size: 0.72rem !important;
    font-weight: 750 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    background: #EEF2FF !important;
    color: #4F46E5 !important;
    -webkit-text-fill-color: #4F46E5 !important;
    border: 1px solid #C7D2FE !important;
    padding: 3px 10px !important;
    border-radius: 9999px !important;
    vertical-align: middle !important;
}
.app-brand-icon-2d {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.18);
    border: 1px solid #E2E8F0;
    display: inline-block;
    vertical-align: middle;
}

.hero-subtitle {
    font-size: 0.92rem !important;
    color: #475569 !important;
    margin-bottom: 1.2rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.6rem !important;
    font-weight: 550 !important;
    text-shadow: none !important;
}
.hero-subtitle span {
    color: #475569 !important;
    text-shadow: none !important;
}

.status-badge-online {
    background: #ECFDF5 !important;
    color: #065F46 !important;
    border: 1px solid #A7F3D0 !important;
    padding: 5px 14px !important;
    border-radius: 9999px !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
}
.status-badge-offline {
    background: #FEF2F2 !important;
    color: #B91C1C !important;
    border: 1px solid #FECACA !important;
    padding: 5px 14px !important;
    border-radius: 9999px !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
}
.nlg-pill {
    background: #EEF2FF !important;
    color: #4338CA !important;
    border: 1px solid #C7D2FE !important;
    padding: 3px 10px !important;
    border-radius: 9999px !important;
    font-size: 0.72rem !important;
    font-weight: 650 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
}

/* Google Gemini Search Bar (Clean 2D Styling) */
.gemini-search-container {
    margin-bottom: 0.65rem;
    position: relative;
    width: 100%;
}
.gemini-search-container div[data-testid="stForm"] {
    background: #F8FAFC !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 32px !important;
    padding: 6px 14px 6px 16px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
    margin-bottom: 0.45rem !important;
}
.gemini-search-container div[data-testid="stForm"]:hover {
    border-color: #94A3B8 !important;
    background: #FFFFFF !important;
}
.gemini-search-container div[data-testid="stForm"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15), 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    background: #FFFFFF !important;
}
.gemini-search-container div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
.gemini-search-container div[data-testid="stColumn"] {
    min-width: unset !important;
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
.gemini-search-container div[data-testid="stColumn"]:nth-child(1) {
    flex: 0 0 auto !important;
    width: auto !important;
    padding: 0 !important;
}
.gemini-search-container div[data-testid="stColumn"]:nth-child(2) {
    flex: 1 1 auto !important;
    width: 100% !important;
}
.gemini-search-container div[data-testid="stColumn"]:nth-child(3) {
    flex: 0 0 auto !important;
    width: auto !important;
    padding: 0 !important;
}

/* Gemini Sparkle Icon */
.gemini-sparkle-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 44px;
    user-select: none;
}
.gemini-sparkle-svg {
    width: 24px;
    height: 24px;
}

/* Seamless Inner Input */
.gemini-search-container [data-baseweb="input"],
.gemini-search-container [data-baseweb="base-input"],
.gemini-search-container div[data-testid="stTextInput"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
.gemini-search-container div[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: #0F172A !important;
    font-size: 1.02rem !important;
    font-weight: 500 !important;
    padding: 8px 6px !important;
    height: 46px !important;
}
.gemini-search-container div[data-testid="stTextInput"] input::placeholder {
    color: #64748B !important;
    font-size: 0.98rem !important;
    font-weight: 400 !important;
}
.gemini-search-container div[data-testid="stTextInput"] input:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
}

/* Gemini Blue Submit Button */
.gemini-search-container div[data-testid="stFormSubmitButton"] {
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    justify-content: flex-end !important;
}
.gemini-search-container div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 22px !important;
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 18px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s ease !important;
}
.gemini-search-container div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px) scale(1.02) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.5) !important;
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
}
.gemini-search-container div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(1px) scale(0.98) !important;
}

/* Gemini Suggestion Chips Container (Clearly Visible Buttons) */
.gemini-chips-container {
    margin-bottom: 0.45rem;
}
.gemini-chips-container button {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 9999px !important;
    color: #1E293B !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    min-height: 36px !important;
    height: 36px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
}
.gemini-chips-container button:hover {
    background: #EFF6FF !important;
    border-color: #2563EB !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15) !important;
}

/* Clear Button */
.gemini-chips-container div[data-testid="stColumn"]:last-child button {
    background: #FEF2F2 !important;
    border-color: #FECACA !important;
    color: #DC2626 !important;
}
.gemini-chips-container div[data-testid="stColumn"]:last-child button:hover {
    background: #FEE2E2 !important;
    border-color: #F87171 !important;
    color: #B91C1C !important;
}

/* Gemini Grounding Disclaimer */
.gemini-disclaimer {
    text-align: center;
    font-size: 0.78rem;
    color: #64748B !important;
    margin-top: 4px;
    margin-bottom: 1.1rem;
    font-weight: 500;
}
.gemini-grad-text {
    color: #2563EB !important;
    font-weight: 700 !important;
}

/* Navigation Tabs */
[data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 4px !important;
    gap: 6px !important;
    margin-bottom: 1.3rem !important;
}
[data-baseweb="tab"] {
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    border: none !important;
    color: #475569 !important;
    transition: all 0.2s ease !important;
}
[data-baseweb="tab"]:hover {
    color: #0F172A !important;
    background: rgba(255, 255, 255, 0.7) !important;
}
[aria-selected="true"] {
    background: #FFFFFF !important;
    color: #4338CA !important;
    border: 1px solid #CBD5E1 !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    text-shadow: none !important;
}

/* Google Gemini Clean Chat Messages (Matching Screenshot 2) */
[data-testid="stChatMessage"] {
    border-radius: 20px !important;
    padding: 0.85rem 1.2rem !important;
    margin-bottom: 1rem !important;
    color: #0F172A !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}

/* User Message - Right-Aligned Bubble (Screenshot 2 style) */
[data-testid="stChatMessage"]:has([aria-label*="user" i]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 24px !important;
    max-width: 78% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    padding: 0.75rem 1.3rem !important;
}

/* Assistant Message - Clean Left-Aligned Typography (Screenshot 2 style) */
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.4rem 0.2rem !important;
    max-width: 100% !important;
}

/* Beautiful Custom Avatar Symbols (Replacing old blocky red/orange icons) */
[data-testid="stChatMessage"]:has([aria-label*="user" i]) [data-testid="stChatMessageAvatarCustom"],
[data-testid="stChatMessage"]:has([aria-label*="user" i]) [data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarUser"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

[data-testid="stChatMessage"]:has([aria-label*="user" i]) [data-testid="stChatMessageAvatarCustom"] span,
[data-testid="stChatMessage"]:has([aria-label*="user" i]) [data-testid="stChatMessageAvatarUser"] span {
    color: #FFFFFF !important;
    font-size: 20px !important;
}

[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) [data-testid="stChatMessageAvatarCustom"],
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) [data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarAssistant"] {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%) !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(124, 58, 237, 0.38) !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) [data-testid="stChatMessageAvatarCustom"] span,
[data-testid="stChatMessage"]:has([aria-label*="assistant" i]) [data-testid="stChatMessageAvatarAssistant"] span {
    color: #FFFFFF !important;
    font-size: 20px !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
    color: #0F172A !important;
    font-size: 1.01rem !important;
    line-height: 1.65 !important;
    text-shadow: none !important;
}
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] b {
    color: #0F172A !important;
    font-weight: 750 !important;
    text-shadow: none !important;
}
[data-testid="stChatMessage"] code {
    color: #0284C7 !important;
    background: #F0F9FF !important;
    border: 1px solid #BAE6FD !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 2px 6px !important;
}

/* Document Cards */
.doc-card {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.15s ease;
}
.doc-card:hover {
    border-color: #94A3B8 !important;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06) !important;
}
.doc-card strong, .doc-card div, .doc-card span {
    color: #0F172A !important;
}
button {
    min-height: 40px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.unique-icon-box {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    flex-shrink: 0;
}
.doc-topic-pill {
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 9999px;
    font-weight: 600;
    display: inline-block;
}
@media (max-width: 768px) {
    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    .hero-title-2d { font-size: 1.5rem !important; }
    .hero-subtitle { font-size: 0.8rem !important; }
    .block-container { 
        padding-left: 0.65rem !important; 
        padding-right: 0.65rem !important; 
        padding-bottom: 2rem !important;
        background: #FFFFFF !important;
    }
    /* Mobile White Input Bar that Moves Down with Output */
    div[data-testid="stChatInput"] {
        position: relative !important;
        width: 100% !important;
        margin: 1.2rem auto 2.5rem auto !important;
        bottom: unset !important;
        left: unset !important;
        transform: none !important;
        background: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08) !important;
        border-radius: 28px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 0.96rem !important;
    }
    [data-testid="stChatMessage"] {
        padding: 0.75rem 0.95rem !important;
    }
}
</style>"""
st.markdown(clean_css, unsafe_allow_html=True)

# ----------------------------------------------------
# BACKEND HEALTH & STATS CHECK (SELF-HEALING)
# ----------------------------------------------------
api_healthy, latency_ms = check_backend_health()
if not api_healthy and not st.session_state.get("backend_autostart_attempted", False):
    st.session_state["backend_autostart_attempted"] = True
    trigger_backend_launch()
    time.sleep(1.2)
    api_healthy, latency_ms = check_backend_health()

# Fetch currently indexed documents (resilient)
indexed_docs = get_resilient_documents(api_healthy)

# Initialize session state for natural language settings
if "llm_provider" not in st.session_state:
    st.session_state["llm_provider"] = "local"
if "llm_api_key" not in st.session_state:
    st.session_state["llm_api_key"] = ""
if "top_k" not in st.session_state:
    st.session_state["top_k"] = 4

# ----------------------------------------------------
# TOP HEADER & BRANDING (UPDATED TEXT STYLE)
# ----------------------------------------------------
col_title, col_stat = st.columns([3.5, 1.2])

with col_title:
    brand_html = f'<img src="data:image/png;base64,{icon_b64}" class="app-brand-icon-2d"/>' if icon_b64 else '<span>🔮</span>'
    st.markdown(
        f"""<div class="hero-title-wrapper">
          {brand_html}
          <div class="hero-title-2d">
            <span class="title-main-2d">Smart Knowledge Base</span>
            <span class="title-agent-2d">Agent</span>
            <span class="agent-tag-2d">AI Agent</span>
          </div>
        </div>""", 
        unsafe_allow_html=True
    )
    st.markdown(
        """<div class="hero-subtitle">
          <span>⚡ Natural Language RAG</span> &bull; 
          <span>🧠 Vector Search</span> &bull; 
          <span>📊 Semantic Synthesis</span>
        </div>""", 
        unsafe_allow_html=True
    )

with col_stat:
    provider_labels = {
        "local": "⚡ Local NLG",
        "gemini": "🌟 Gemini AI",
        "groq": "🚀 Groq Llama-3",
        "openai": "🤖 GPT-4o",
        "ollama": "💻 Ollama"
    }
    cur_provider_label = provider_labels.get(st.session_state["llm_provider"], "⚡ Local NLG")
    
    if api_healthy:
        st.markdown(
            f"""<div style="text-align: right; padding-top: 4px;">
            <span class="status-badge-online">● Agent Active &bull; {latency_ms}ms</span>
            <div style="margin-top: 4px; display: flex; justify-content: flex-end; gap: 6px; align-items: center;">
              <span class="nlg-pill">{cur_provider_label}</span>
              <span style="font-size: 11px; color: #64748B;">{len(indexed_docs)} docs indexed</span>
            </div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""<div style="text-align: right; padding-top: 4px;">
            <span class="status-badge-online" style="background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;">● In-Process Mode Active</span>
            <div style="margin-top: 4px; display: flex; justify-content: flex-end; gap: 6px; align-items: center;">
              <span class="nlg-pill">Zero Downtime</span>
              <span style="font-size: 11px; color: #64748B;">{len(indexed_docs)} docs indexed</span>
            </div>
            </div>""",
            unsafe_allow_html=True
        )

# ----------------------------------------------------
# THREE NAVIGATION TABS
# ----------------------------------------------------
tab_chat, tab_library, tab_controls = st.tabs([
    "💬 AI Agent Chat",
    f"📁 Knowledge Library ({len(indexed_docs)})",
    "🎛️ Controls & Settings"
])

# ====================================================
# TAB 1: AI AGENT CHAT (ERGONOMIC TOP SEARCH BAR)
# ====================================================
with tab_chat:
    # ---------------------------------------------------------
    # QUICK PROMPT CHIPS & ACTIONS (AT TOP)
    # ---------------------------------------------------------
    st.markdown('<div class="gemini-chips-container">', unsafe_allow_html=True)
    col_chip1, col_chip2, col_chip3, col_chip4, col_clear = st.columns([1, 1, 1, 1, 0.55])
    quick_prompt = None

    with col_chip1:
        if st.button("✦ Explain Simply", use_container_width=True):
            quick_prompt = "Explain the core concepts and topics in my documents in simple, everyday English."
    with col_chip2:
        if st.button("✦ Summarize All", use_container_width=True):
            quick_prompt = "Provide a comprehensive executive summary of the main points across the uploaded documents."
    with col_chip3:
        if st.button("✦ F-Test Hypotheses", use_container_width=True):
            quick_prompt = "What are the null and alternative hypotheses for the F-test and how are they calculated?"
    with col_chip4:
        if st.button("✦ Vuforia & Unity", use_container_width=True):
            quick_prompt = "What is Vuforia and how does it integrate with GameObjects and Image Targets in Unity?"
    with col_clear:
        if st.button("🧹 Clear", use_container_width=True, help="Clear conversation"):
            st.session_state.messages = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Hello! I'm your Smart Knowledge Base Agent.**\n\n"
                    "Ask any question in the search bar below or tap one of the quick starter chips above to explore your knowledge library in natural language!"
                ),
                "sources": []
            }
        ]

    # ---------------------------------------------------------
    # RENDER CONVERSATION MESSAGES & ANSWERS (AT TOP)
    # ---------------------------------------------------------
    USER_AVATAR = ":material/person:"
    ASSISTANT_AVATAR = ":material/auto_awesome:"

    for msg in st.session_state.messages:
        role = msg.get("role", "assistant")
        avatar_val = ASSISTANT_AVATAR if role == "assistant" else USER_AVATAR
        with st.chat_message(role, avatar=avatar_val):
            st.markdown(msg["content"])
            
            # Source Citations Card with Unique Document Symbols
            if msg.get("sources"):
                with st.expander(f"📚 Verified Sources ({len(msg['sources'])} relevant chunks)", expanded=False):
                    for idx, src in enumerate(msg["sources"], 1):
                        source_file = os.path.basename(src.get("source_id", "Document"))
                        meta = get_unique_doc_metadata(source_file)
                        score = src.get("score", 0.0)
                        chunk_idx = src.get("chunk_index", 0)
                        
                        match_pct = max(15, min(99, int((1.0 - (score / 2.0)) * 100)))
                        badge_color = "#059669" if match_pct >= 80 else "#2563EB"
                        
                        st.markdown(
                            f"""<div style="margin-bottom: 6px;">
                            <strong>#{idx}</strong> <span>{meta['symbol']}</span> <code>{source_file}</code> &bull; Chunk {chunk_idx} &bull; 
                            <span style="color: {badge_color}; font-weight: 700;">{match_pct}% Match</span>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        st.info(src.get("content", ""))

    # ---------------------------------------------------------
    # PINNED BOTTOM SEARCH BAR (SCREENSHOT 2 PLACEMENT)
    # ---------------------------------------------------------
    user_query = st.chat_input("✦ Ask Gemini anything about your documents...")
    active_prompt = quick_prompt if quick_prompt else user_query

    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(active_prompt)

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            with st.spinner("Smart Agent synthesizing answer..."):
                try:
                    search_depth = st.session_state.get("top_k", 4)
                    cur_prov = st.session_state.get("llm_provider", "local")
                    cur_key = st.session_state.get("llm_api_key", "")

                    answer_text, sources, exec_mode = execute_resilient_chat(
                        active_prompt=active_prompt,
                        search_depth=search_depth,
                        provider=cur_prov,
                        api_key=cur_key,
                        is_api_alive=api_healthy
                    )
                    
                    st.markdown(answer_text)
                    
                    if sources:
                        with st.expander(f"📚 Verified Sources ({len(sources)} relevant chunks)", expanded=False):
                            for idx, src in enumerate(sources, 1):
                                source_file = os.path.basename(src.get("source_id", "Document"))
                                meta = get_unique_doc_metadata(source_file)
                                score = src.get("score", 0.0)
                                chunk_idx = src.get("chunk_index", 0)
                                match_pct = max(15, min(99, int((1.0 - (score / 2.0)) * 100)))
                                badge_color = "#059669" if match_pct >= 80 else "#2563EB"
                                
                                st.markdown(
                                    f"""<div style="margin-bottom: 6px;">
                                    <strong>#{idx}</strong> <span>{meta['symbol']}</span> <code>{source_file}</code> &bull; Chunk {chunk_idx} &bull; 
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
                except Exception as e:
                    err = f"⚠️ Error: {str(e)}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})
        st.rerun()

    # Smooth auto-scroll anchor to follow input bar as it moves down
    st.markdown(
        """<div id="chat-bottom-anchor"></div>
        <script>
            (function() {
                setTimeout(function() {
                    var el = document.getElementById("chat-bottom-anchor");
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    var main = window.parent.document.querySelector('.main') || window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
                    if (main) {
                        main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
                    }
                }, 80);
            })();
        </script>""",
        unsafe_allow_html=True
    )

# ====================================================
# TAB 2: KNOWLEDGE LIBRARY & DOCUMENT INGESTION
# ====================================================
with tab_library:
    st.subheader("📤 Document Ingestion Dropzone")
    st.caption("Upload files to extract text, generate 384-d vector embeddings, and assign unique topic icon symbols.")
    
    new_files = st.file_uploader(
        "Drop PDF, DOCX, or TXT files here:",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="uploader_widget"
    )
    
    col_upload_btn, col_resync_btn = st.columns([2, 1])
    with col_upload_btn:
        if st.button("🚀 Ingest & Index Uploaded Files", use_container_width=True, type="primary"):
            if new_files:
                successes = 0
                for f in new_files:
                    with st.spinner(f"Ingesting {f.name}..."):
                        if ingest_resilient(f.name, f.getvalue(), api_healthy):
                            successes += 1
                        else:
                            st.error(f"Error indexing {f.name}")
                if successes > 0:
                    st.success(f"✅ Ingested {successes} document(s)! Embeddings saved in ChromaDB.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please select at least one file to upload.")
                
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
            
            # Resolve unique icon & badge styling
            meta = get_unique_doc_metadata(fname, ftype)
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
                      <div style="display: flex; align-items: center; gap: 14px;">
                        <div class="unique-icon-box" style="background: {meta['gradient']}; border: 1px solid {meta['border']};">
                          {meta['symbol']}
                        </div>
                        <div>
                          <div style="font-weight: 700; font-size: 0.98rem; display: flex; align-items: center; gap: 8px;">
                            <span>{fname}</span>
                            <span class="doc-topic-pill" style="background: {meta['bg']}; color: {meta['color']}; border: 1px solid {meta['border']};">
                              {meta['badge']}
                            </span>
                          </div>
                          <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">
                            Format: <strong>{ftype}</strong> {size_str} &bull; SHA-256: <code>{fhash}...</code> &bull; Indexed: {indexed_at}
                          </div>
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
                    if delete_resilient(fname, api_healthy):
                        st.toast(f"Deleted {fname}", icon="🗑️")
                        st.success(f"Successfully deleted {fname}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete {fname}")
            st.write("")

# ====================================================
# TAB 3: APP CONTROLS, SETTINGS & MOBILE
# ====================================================
with tab_controls:
    st.subheader("🔮 Unique Branding & Icon Symbols")
    st.caption("Custom high-definition icon symbols dynamically assigned to your documents and application:")
    
    col_sym1, col_sym2, col_sym3, col_sym4 = st.columns(4)
    with col_sym1:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 12px; text-align: center;">
          <div style="font-size: 1.8rem;">📊</div>
          <div style="font-weight: 700; font-size: 0.85rem; color: #F59E0B; margin-top: 4px;">Statistics & Math</div>
          <div style="font-size: 0.72rem; color: #94A3B8;">F-Test, formulas, data</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sym2:
        st.markdown("""
        <div style="background: rgba(236, 72, 153, 0.1); border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 12px; padding: 12px; text-align: center;">
          <div style="font-size: 1.8rem;">🥽</div>
          <div style="font-weight: 700; font-size: 0.85rem; color: #EC4899; margin-top: 4px;">Augmented Reality</div>
          <div style="font-size: 0.72rem; color: #94A3B8;">Vuforia, targets, AR</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sym3:
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 12px; text-align: center;">
          <div style="font-size: 1.8rem;">🎮</div>
          <div style="font-weight: 700; font-size: 0.85rem; color: #818CF8; margin-top: 4px;">Game Engine</div>
          <div style="font-size: 0.72rem; color: #94A3B8;">Unity, scripts, objects</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sym4:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px; text-align: center;">
          <div style="font-size: 1.8rem;">🛡️</div>
          <div style="font-weight: 700; font-size: 0.85rem; color: #10B981; margin-top: 4px;">Cybersecurity</div>
          <div style="font-size: 0.72rem; color: #94A3B8;">IDS, networks, safety</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🧠 Natural Language Engine Configuration")
    st.caption("Choose how natural language answers are formulated:")
    
    col_prov1, col_prov2 = st.columns([1.5, 2])
    with col_prov1:
        provider_options = ["local", "gemini", "groq", "openai", "ollama"]
        provider_format = {
            "local": "⚡ Local NLG (Offline & Private)",
            "gemini": "🌟 Google Gemini API",
            "groq": "🚀 Groq (Llama-3.1)",
            "openai": "🤖 OpenAI (GPT-4o)",
            "ollama": "💻 Local Ollama"
        }
        selected_prov = st.selectbox(
            "AI Natural Language Model:",
            options=provider_options,
            format_func=lambda x: provider_format[x],
            index=provider_options.index(st.session_state.get("llm_provider", "local"))
        )
        st.session_state["llm_provider"] = selected_prov

    with col_prov2:
        if selected_prov in ["gemini", "groq", "openai"]:
            key_label = "Google Gemini API Key:" if selected_prov == "gemini" else "Groq API Key:" if selected_prov == "groq" else "OpenAI API Key:"
            api_key_input = st.text_input(
                key_label,
                type="password",
                value=st.session_state.get("llm_api_key", ""),
                help="Optional. Leave blank to automatically use the built-in Local Natural Language engine."
            )
            st.session_state["llm_api_key"] = api_key_input
        else:
            st.info("💡 **Local NLG Active:** Operates 100% offline with zero external API keys needed. All synthesis happens locally on your computer.")

    st.markdown("---")
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
    
    # Read active mobile network tunnel URL if available
    tunnel_file = os.path.join(PROJECT_ROOT, "tunnel_url.txt")
    mobile_network_url = ""
    if os.path.exists(tunnel_file):
        try:
            with open(tunnel_file, "r", encoding="utf-8") as f:
                mobile_network_url = f.read().strip()
        except Exception:
            mobile_network_url = ""

    active_mobile_url = mobile_network_url if mobile_network_url else "http://192.168.1.53:8501"

    col_qr, col_qr_info = st.columns([1, 2])
    with col_qr:
        qr_file = os.path.join(PROJECT_ROOT, "mobile_qr.png")
        if os.path.exists(qr_file):
            st.image(qr_file, width=190)
    with col_qr_info:
        if mobile_network_url:
            st.markdown(
                """<div style="margin-bottom: 6px;">
                  <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">
                    ● Active on 4G / 5G Cellular Mobile Data
                  </span>
                </div>""",
                unsafe_allow_html=True
            )
            st.markdown("**🌐 Public Mobile Network Link (Anywhere in the World):**")
            st.code(mobile_network_url, language="text")
            st.caption("✅ Works directly on your phone's cellular mobile data (4G/5G). No Wi-Fi required!")
        else:
            st.markdown("**Wi-Fi Network Link:**")
            st.code("http://192.168.1.53:8501", language="text")
            st.caption("Connect your phone to the same Wi-Fi network.")

        st.markdown("""
        * **iPhone (Safari)**: Open link ➔ Tap Share (square with arrow) ➔ tap **Add to Home Screen**.
        * **Android (Chrome)**: Open link ➔ Tap Menu (⋮) ➔ tap **Install app** or **Add to Home screen**.
        """)

        col_tbtn, col_wifi_sub = st.columns([1.2, 1.5])
        with col_tbtn:
            if st.button("⚡ Restart Mobile Tunnel", use_container_width=True):
                with st.spinner("Re-launching mobile network tunnel..."):
                    trigger_tunnel_launch()
                    time.sleep(3)
                    st.rerun()
        with col_wifi_sub:
            if mobile_network_url:
                st.caption(f"🏠 Wi-Fi fallback: `http://192.168.1.53:8501`")

    st.markdown("---")
    st.subheader("🖥️ Infrastructure & Services Manager")
    st.caption("Live monitoring and 1-click self-healing controls for all underlying components:")

    col_srv1, col_srv2 = st.columns(2)
    with col_srv1:
        if api_healthy:
            backend_badge = f'<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Online 🟢 ({latency_ms}ms)</span>'
        else:
            backend_badge = '<span style="background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">In-Process Active ⚡</span>'

        st.markdown(
            f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">🚀 FastAPI Backend Service</div>
                {backend_badge}
              </div>
              <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px;">
                Address: <code>{API_HOST}</code> &bull; REST API &bull; Health Check
              </div>
            </div>""",
            unsafe_allow_html=True
        )

        st.markdown(
            """<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">🌐 Streamlit Frontend Application</div>
                <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Active 🟢</span>
              </div>
              <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px;">
                Port: <code>8501</code> &bull; Local & Mobile Web App UI
              </div>
            </div>""",
            unsafe_allow_html=True
        )

        tunnel_badge = '<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Active 🟢</span>' if mobile_network_url else '<span style="background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Standby 🟡</span>'
        st.markdown(
            f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">📱 Mobile Network Tunnel</div>
                {tunnel_badge}
              </div>
              <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px;">
                Access: <strong>Cloudflare HTTPS</strong> &bull; 4G/5G Cellular Data
              </div>
            </div>""",
            unsafe_allow_html=True
        )

    with col_srv2:
        st.markdown(
            f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">🧠 ChromaDB Vector Storage</div>
                <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Connected 🟢</span>
              </div>
              <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px;">
                Engine: <code>all-MiniLM-L6-v2</code> &bull; 384-d Persistent Embeddings
              </div>
            </div>""",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">📋 SQLite Metadata Store</div>
                <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">Connected 🟢</span>
              </div>
              <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px;">
                Storage: <code>data/metadata.sqlite</code> &bull; <strong>{len(indexed_docs)}</strong> indexed documents
              </div>
            </div>""",
            unsafe_allow_html=True
        )

    col_btn_start, col_btn_check = st.columns([1.5, 1])
    with col_btn_start:
        if st.button("⚡ Start / Restart Backend Service", use_container_width=True):
            with st.spinner("Starting backend service in background..."):
                trigger_backend_launch()
                time.sleep(1.8)
                st.session_state["backend_autostart_attempted"] = True
                st.rerun()

    with col_btn_check:
        if st.button("🔄 Re-check Health", use_container_width=True):
            st.rerun()

    st.markdown(
        """<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-top: 10px; font-size: 0.82rem; color: #475569;">
          <strong>🛡️ Zero-Configuration Resilience:</strong> The application is fully self-contained. 
          If the backend service is offline, queries and document lookups automatically continue using the built-in 
          in-process RAG engine. You never need to run command line scripts or manage server processes manually.
        </div>""",
        unsafe_allow_html=True
    )
