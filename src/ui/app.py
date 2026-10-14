import streamlit as st
import requests
import os
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

# Mobile Web App PWA Manifest
pwa_manifest = {
    "name": "Gemini AI Agent",
    "short_name": "Gemini",
    "description": "Smart Knowledge Base AI Assistant",
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

# Unique Document Icon & Metadata Resolver
def get_unique_doc_metadata(filename: str, ftype: str = "") -> dict:
    fname_lower = filename.lower()
    if any(k in fname_lower for k in ["f_test", "ftest", "stat", "hypothesis", "variance", "math", "calc", "prob"]):
        return {
            "symbol": "📊",
            "badge": "Statistics & Math",
            "color": "#D97706",
            "bg": "rgba(245, 158, 11, 0.12)",
            "border": "rgba(245, 158, 11, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(217, 119, 6, 0.1))"
        }
    elif any(k in fname_lower for k in ["vuforia", "ar", "augmented", "target", "vision"]):
        return {
            "symbol": "🥽",
            "badge": "Augmented Reality",
            "color": "#DB2777",
            "bg": "rgba(236, 72, 153, 0.12)",
            "border": "rgba(236, 72, 153, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(219, 39, 119, 0.1))"
        }
    elif any(k in fname_lower for k in ["unity", "game", "physics", "gameobject", "script"]):
        return {
            "symbol": "🎮",
            "badge": "Game Engine",
            "color": "#4F46E5",
            "bg": "rgba(99, 102, 241, 0.12)",
            "border": "rgba(99, 102, 241, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(79, 70, 229, 0.1))"
        }
    elif any(k in fname_lower for k in ["ids", "security", "network", "cyber", "firewall", "crypto"]):
        return {
            "symbol": "🛡️",
            "badge": "Cybersecurity",
            "color": "#059669",
            "bg": "rgba(16, 185, 129, 0.12)",
            "border": "rgba(16, 185, 129, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.1))"
        }
    elif any(k in fname_lower for k in ["doctor", "hospital", "clinic", "health", "medical"]):
        return {
            "symbol": "🩺",
            "badge": "Healthcare & Clinic",
            "color": "#2563EB",
            "bg": "rgba(37, 99, 235, 0.12)",
            "border": "rgba(37, 99, 235, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(29, 78, 216, 0.1))"
        }
    elif ftype.upper() == "PDF":
        return {
            "symbol": "📕",
            "badge": "PDF Document",
            "color": "#DC2626",
            "bg": "rgba(239, 68, 68, 0.12)",
            "border": "rgba(239, 68, 68, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(220, 38, 38, 0.1))"
        }
    elif ftype.upper() == "DOCX":
        return {
            "symbol": "📘",
            "badge": "Word Document",
            "color": "#0284C7",
            "bg": "rgba(56, 189, 248, 0.12)",
            "border": "rgba(56, 189, 248, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(37, 99, 235, 0.1))"
        }
    else:
        return {
            "symbol": "📑",
            "badge": "Knowledge File",
            "color": "#7C3AED",
            "bg": "rgba(168, 85, 247, 0.12)",
            "border": "rgba(168, 85, 247, 0.35)",
            "gradient": "linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(147, 51, 234, 0.1))"
        }

# Streamlit Page Config - Responsive Layout (Auto-sidebar on mobile)
st.set_page_config(
    page_title="Gemini",
    page_icon=ICON_PATH if os.path.exists(ICON_PATH) else "✦",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom Authentic Google Gemini Theme & Typography + Mobile App Enhancements
gemini_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Roboto+Mono:wght@400;500&display=swap');

#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden;
    display: none !important;
}

html, body, [class*="css"] {
    font-family: 'Google Sans', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: #FFFFFF !important;
    color: #1F1F1F !important;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
}

/* =========================================================
   GOOGLE GEMINI SIDEBAR STYLING
   ========================================================= */
[data-testid="stSidebar"] {
    background-color: #F0F4F9 !important;
    border-right: 1px solid #E3E8EE !important;
    min-width: 270px !important;
    max-width: 300px !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background-color: #F0F4F9 !important;
    padding-top: 0.8rem !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
}

/* Mobile Sidebar Toggle Button */
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    top: 0.65rem !important;
    left: 0.65rem !important;
    background: #F0F4F9 !important;
    border: 1px solid #D3D7DC !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    z-index: 999999 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
}
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #1F1F1F !important;
    width: 20px !important;
    height: 20px !important;
}

.gemini-sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0.6rem 0.8rem 0.6rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    margin-bottom: 0.6rem;
}
.gemini-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    text-decoration: none;
}
.gemini-brand-text {
    font-size: 1.35rem;
    font-weight: 600;
    color: #1F1F1F;
    letter-spacing: -0.01em;
}
.gemini-brand-icon {
    width: 26px;
    height: 26px;
}
.gemini-sidebar-icons {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #444746;
    font-size: 1.05rem;
}

.sidebar-section-title {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #72777A;
    padding: 10px 10px 4px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* User Account Profile Footer in Sidebar */
.gemini-user-profile {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-top: 1px solid #E3E8EE;
    margin-top: 1.2rem;
    border-radius: 12px;
    background: transparent;
}
.gemini-user-info {
    display: flex;
    align-items: center;
    gap: 10px;
}
.gemini-user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4285F4 0%, #9B72CB 50%, #D96570 100%);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.88rem;
}
.gemini-user-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1F1F1F;
    line-height: 1.1;
}
.gemini-user-badge {
    font-size: 0.72rem;
    color: #5E5E5E;
    font-weight: 500;
}

/* =========================================================
   MAIN VIEW & TOP NAVIGATION
   ========================================================= */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 8.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 950px !important;
    margin: 0 auto !important;
}

.gemini-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #F1F5F9;
    margin-bottom: 1rem;
}
.gemini-chat-title {
    font-size: 1.35rem;
    font-weight: 600;
    color: #1F1F1F;
    letter-spacing: -0.015em;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* =========================================================
   EXACT GEMINI CHAT RESPONSE FORMATTING
   ========================================================= */
.gemini-code-container {
    background: #181C20;
    border-radius: 16px;
    overflow: hidden;
    margin: 1rem 0;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    max-width: 100%;
}
.gemini-code-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: #212529;
    color: #C4C7C5;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #2D3135;
}
.gemini-code-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}
.gemini-code-body {
    padding: 14px 18px;
    color: #E3E3E3;
    font-family: 'Roboto Mono', Consolas, monospace;
    font-size: 0.92rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* Gemini Quoted Prompt Card */
.gemini-prompt-quote {
    border-left: 2px dashed #CBD5E1;
    background: #F8FAFC;
    padding: 14px 18px;
    border-radius: 0 12px 12px 0;
    font-size: 0.95rem;
    color: #334155;
    line-height: 1.6;
    margin: 1rem 0;
}

/* Gemini Action Footer (Thumbs Up, Down, Retry, Copy, More) */
.gemini-action-row {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #5E5E5E;
    font-size: 1.05rem;
    padding-top: 8px;
    padding-bottom: 8px;
}
.gemini-action-btn {
    cursor: pointer;
    transition: color 0.15s ease;
    user-select: none;
}
.gemini-action-btn:hover {
    color: #1F1F1F;
}

/* =========================================================
   FLOATING GEMINI PILL SEARCH BAR (PINNED BOTTOM)
   ========================================================= */
[data-testid="stBottomBlockContainer"] {
    visibility: visible !important;
    display: block !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.95) 25%, #FFFFFF 100%) !important;
    padding-bottom: max(0.6rem, env(safe-area-inset-bottom, 0.6rem)) !important;
    padding-top: 0.6rem !important;
    max-width: 950px !important;
    margin: 0 auto !important;
}

[data-testid="stChatInput"] {
    border: 1px solid #D3D7DC !important;
    border-radius: 9999px !important;
    background: #F0F4F9 !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04) !important;
    padding: 6px 16px 6px 20px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #A8C7FA !important;
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.15), 0 4px 18px rgba(0, 0, 0, 0.08) !important;
    background: #FFFFFF !important;
}
[data-testid="stChatInput"] textarea {
    color: #1F1F1F !important;
    font-size: 16px !important; /* Critical: Prevents automatic zoom on iPhone & Android */
    font-weight: 450 !important;
    padding-top: 8px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #5E5E5E !important;
    font-size: 1.0rem !important;
    font-weight: 400 !important;
}
[data-testid="stChatInput"] button {
    background: transparent !important;
    color: #444746 !important;
    border-radius: 50% !important;
    width: 38px !important;
    height: 38px !important;
    border: none !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover {
    background: #E1E8F2 !important;
    color: #1F1F1F !important;
    transform: scale(1.05) !important;
}
[data-testid="stChatInput"] button svg {
    fill: #1F1F1F !important;
}

.gemini-disclaimer-text {
    text-align: center;
    font-size: 0.74rem;
    color: #72777A;
    margin-top: 4px;
    margin-bottom: 2px;
}

/* =========================================================
   MOBILE RESPONSIVENESS & TOUCH OPTIMIZATIONS (< 768px)
   ========================================================= */
@media (max-width: 768px) {
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 7.2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }

    .gemini-chat-title {
        font-size: 1.12rem !important;
        line-height: 1.25 !important;
    }

    /* Full width bottom input on mobile */
    [data-testid="stBottomBlockContainer"] {
        padding-bottom: max(0.5rem, env(safe-area-inset-bottom, 0.5rem)) !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        padding-top: 0.4rem !important;
        width: 100% !important;
    }
    [data-testid="stChatInput"] {
        padding: 4px 10px 4px 16px !important;
    }

    /* Touch target sizes for action icons */
    .gemini-action-row {
        gap: 22px !important;
        font-size: 1.25rem !important;
        padding: 8px 4px !important;
    }
    .gemini-action-btn {
        padding: 4px 6px !important;
    }

    /* Mobile Code Snippets */
    .gemini-code-container {
        border-radius: 12px !important;
        margin: 0.6rem 0 !important;
    }
    .gemini-code-header {
        padding: 8px 12px !important;
        font-size: 0.75rem !important;
    }
    .gemini-code-body {
        font-size: 0.82rem !important;
        padding: 10px 12px !important;
    }

    /* Mobile navigation buttons */
    div[data-testid="stColumn"] button {
        min-height: 38px !important;
        padding: 4px 6px !important;
        font-size: 0.8rem !important;
    }

    .gemini-disclaimer-text {
        font-size: 0.68rem !important;
        margin-top: 2px !important;
    }
}
</style>"""

pwa_tags = f"""
<link rel="manifest" href="data:application/manifest+json;base64,{manifest_b64}">
<meta name="theme-color" content="#FFFFFF">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Gemini">
<link rel="apple-touch-icon" href="data:image/png;base64,{icon_b64}">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
"""

st.markdown(gemini_css + pwa_tags, unsafe_allow_html=True)

# ----------------------------------------------------
# SYSTEM STATE & ACTIVE VIEW ROUTING
# ----------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "chat"

if "active_chat_title" not in st.session_state:
    st.session_state["active_chat_title"] = "Chennai Doctor Dataset for Website"

if "llm_provider" not in st.session_state:
    st.session_state["llm_provider"] = "local"

if "llm_api_key" not in st.session_state:
    st.session_state["llm_api_key"] = ""

if "top_k" not in st.session_state:
    st.session_state["top_k"] = 4

# Check backend health & fetch documents
api_healthy = False
indexed_docs = []
try:
    health_res = requests.get(f"{API_HOST}/health", timeout=2)
    if health_res.status_code == 200:
        api_healthy = True
except Exception:
    api_healthy = False

if api_healthy:
    try:
        docs_res = requests.get(f"{API_HOST}/documents", timeout=3)
        if docs_res.status_code == 200:
            indexed_docs = docs_res.json().get("documents", [])
    except Exception:
        indexed_docs = []

# Google Gemini Sparkle SVG Logo
gemini_sparkle_svg = """
<svg class="gemini-brand-icon" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 0C14 7.73199 7.73199 14 0 14C7.73199 14 14 20.268 14 28C14 20.268 20.268 14 28 14C20.268 14 14 7.73199 14 0Z" fill="url(#gemini_grad)"/>
  <defs>
    <linearGradient id="gemini_grad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4285F4"/>
      <stop offset="35%" stop-color="#9B72CB"/>
      <stop offset="70%" stop-color="#D96570"/>
      <stop offset="100%" stop-color="#F2994A"/>
    </linearGradient>
  </defs>
</svg>
"""

# ====================================================
# LEFT SIDEBAR: AUTHENTIC GOOGLE GEMINI NAVIGATION
# ====================================================
with st.sidebar:
    # Gemini Header with brand & icons
    st.markdown(
        f"""<div class="gemini-sidebar-header">
          <div class="gemini-brand">
            {gemini_sparkle_svg}
            <span class="gemini-brand-text">Gemini</span>
          </div>
          <div class="gemini-sidebar-icons">
            <span>🔍</span>
            <span>◨</span>
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    # + New Chat Action Button
    if st.button("✏️  New chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state["active_chat_title"] = "New Conversation"
        st.session_state["active_view"] = "chat"
        st.rerun()

    st.markdown('<div style="margin-top: 6px;"></div>', unsafe_allow_html=True)

    # Top Menu Items (Matching Screenshot)
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🎨 Images", use_container_width=True):
            st.session_state["active_view"] = "chat"
            st.rerun()
    with col_nav2:
        if st.button("⏰ Scheduled", use_container_width=True):
            st.toast("No scheduled tasks yet.")

    col_nav3, col_nav4 = st.columns(2)
    with col_nav3:
        if st.button("🎓 Students", use_container_width=True):
            st.session_state["active_view"] = "chat"
            st.rerun()
    with col_nav4:
        if st.button("⋯ More", use_container_width=True):
            st.session_state["active_view"] = "settings"
            st.rerun()

    st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)

    # Section 1: Notebooks (Knowledge Base Documents)
    st.markdown(
        """<div class="sidebar-section-title">
          <span>Notebooks</span>
          <span style="font-size: 0.75rem; color: #2563EB;">✦</span>
        </div>""",
        unsafe_allow_html=True
    )

    if st.button("➕ New notebook / Add Doc", use_container_width=True):
        st.session_state["active_view"] = "library"
        st.rerun()

    # Dynamic or default notebooks
    if indexed_docs:
        for d in indexed_docs[:3]:
            fname = d.get("filename") or os.path.basename(d.get("source_id", "Doc"))
            meta = get_unique_doc_metadata(fname, d.get("source_type", ""))
            short_name = (fname[:22] + '...') if len(fname) > 22 else fname
            if st.button(f"{meta['symbol']} {short_name}", key=f"nb_{fname}", use_container_width=True):
                st.session_state["active_chat_title"] = fname
                st.session_state["active_view"] = "chat"
                st.rerun()
    else:
        sample_notebooks = [
            ("📘", "IoT Management and Sec..."),
            ("📗", "Finite Automata and Reg..."),
            ("📙", "Computer Architecture: R...")
        ]
        for sym, name in sample_notebooks:
            if st.button(f"{sym} {name}", key=f"snb_{name}", use_container_width=True):
                st.session_state["active_chat_title"] = name
                st.session_state["active_view"] = "chat"
                st.rerun()

    st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)

    # Section 2: Recent Chats ("All")
    st.markdown(
        """<div class="sidebar-section-title">
          <span>All</span>
          <span>🝖</span>
        </div>""",
        unsafe_allow_html=True
    )

    recent_topics = [
        "Chennai Doctor Dataset for Website",
        "Efficient Algorithm Complexity Goal",
        "Understanding the Term Pro",
        "Antigravity IDE Screenshot Overview",
        "Song Lyrics Search Assistance"
    ]

    for topic in recent_topics:
        is_active = (st.session_state.get("active_chat_title") == topic)
        btn_label = f"💬 {topic}" if not is_active else f"✦ {topic}"
        if st.button(btn_label, key=f"rec_{topic}", use_container_width=True):
            st.session_state["active_chat_title"] = topic
            st.session_state["active_view"] = "chat"
            st.rerun()

    # User Profile / Account Card at Sidebar Footer
    st.markdown(
        """<div class="gemini-user-profile">
          <div class="gemini-user-info">
            <div class="gemini-user-avatar">S</div>
            <div>
              <div class="gemini-user-name">Sivasaigolla</div>
              <div class="gemini-user-badge">Pro &bull; Online</div>
            </div>
          </div>
          <div style="font-size: 1.15rem; color: #444746; cursor: pointer;">⚙️</div>
        </div>""",
        unsafe_allow_html=True
    )
    if st.button("⚙️ Open Settings & Models", use_container_width=True):
        st.session_state["active_view"] = "settings"
        st.rerun()


# ====================================================
# RESPONSIVE TOP BAR (ACTIVE CHAT TITLE & VIEW SWITCHERS)
# ====================================================
col_title, col_actions = st.columns([1.7, 1.3])
with col_title:
    st.markdown(
        f"""<div class="gemini-top-bar">
          <div class="gemini-chat-title">{gemini_sparkle_svg} <span>{st.session_state['active_chat_title']}</span></div>
        </div>""",
        unsafe_allow_html=True
    )

with col_actions:
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.15, 0.95])
    with c_btn1:
        if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state["active_view"] == "chat" else "secondary"):
            st.session_state["active_view"] = "chat"
            st.rerun()
    with c_btn2:
        doc_count = len(indexed_docs)
        if st.button(f"📁 Docs ({doc_count})", use_container_width=True, type="primary" if st.session_state["active_view"] == "library" else "secondary"):
            st.session_state["active_view"] = "library"
            st.rerun()
    with c_btn3:
        if st.button("⚙️ Setup", use_container_width=True, type="primary" if st.session_state["active_view"] == "settings" else "secondary"):
            st.session_state["active_view"] = "settings"
            st.rerun()


# ====================================================
# VIEW 1: GEMINI CHAT INTERFACE (MATCHING SCREENSHOT)
# ====================================================
if st.session_state["active_view"] == "chat":
    # Initialize Messages with the Exact Screenshot Example if brand new
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "assistant",
                "is_example": True,
                "content": (
                    "**Prompt for Antigravity (Location & Distance Search)**\n\n"
                    "Now that your data has explicit addresses, landmarks, and coordinates, you can ask Antigravity to build a \"Search by Distance\" feature. Try this prompt:"
                ),
                "code_snippet": '[\n  {\n    "consultation_fee_inr": 800,\n    "rating": 4.6\n  }\n]',
                "prompt_quote": (
                    '"I am updating my doctor appointment app database. Here is a JSON array of doctors that now includes a '
                    'nested \'location\' object with \'full_address\', \'landmark\', and latitude/longitude \'coordinates\'. '
                    'Please update my SQLAlchemy models to store this location data. Then, write a function that calculates '
                    'the distance between a user\'s latitude/longitude and the clinic\'s coordinates, and sorts the doctors from nearest to farthest."'
                ),
                "sources": []
            }
        ]

    # Render Conversation Messages matching Google Gemini Style
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{msg['content']}**")
        else:
            with st.chat_message("assistant", avatar="✦"):
                # Render JSON / Code box if present
                if msg.get("code_snippet"):
                    st.markdown(
                        f"""<div class="gemini-code-container">
                          <div class="gemini-code-header">
                            <span>JSON</span>
                            <div class="gemini-code-actions">
                              <span>📥</span>
                              <span>📋</span>
                            </div>
                          </div>
                          <div class="gemini-code-body">{msg['code_snippet']}</div>
                        </div>""",
                        unsafe_allow_html=True
                    )

                # Render Main Explanation / Response
                st.markdown(msg["content"])

                # Render Prompt Callout Quote if present
                if msg.get("prompt_quote"):
                    st.markdown(
                        f"""<div class="gemini-prompt-quote">
                          {msg['prompt_quote']}
                        </div>""",
                        unsafe_allow_html=True
                    )

                # Gemini Feedback Action Row: Thumbs Up, Down, Retry, Copy, More
                st.markdown(
                    """<div class="gemini-action-row">
                      <span class="gemini-action-btn" title="Good response">👍</span>
                      <span class="gemini-action-btn" title="Bad response">👎</span>
                      <span class="gemini-action-btn" title="Regenerate">🔄</span>
                      <span class="gemini-action-btn" title="Copy text">📋</span>
                      <span class="gemini-action-btn" title="More options">⋯</span>
                    </div>""",
                    unsafe_allow_html=True
                )

                # Verified Sources Expander
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
    # PINNED GEMINI INPUT CAPSULE (SEARCH DOWN)
    # ---------------------------------------------------------
    user_query = st.chat_input("Ask Gemini")

    if user_query and user_query.strip():
        # Update chat title if still default
        if st.session_state["active_chat_title"] == "New Conversation":
            st.session_state["active_chat_title"] = user_query.strip()[:32]

        st.session_state.messages.append({"role": "user", "content": user_query.strip()})
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{user_query.strip()}**")

        with st.chat_message("assistant", avatar="✦"):
            with st.spinner("Gemini is synthesizing answer..."):
                try:
                    search_depth = st.session_state.get("top_k", 4)
                    chat_payload = {
                        "query": user_query.strip(),
                        "top_k": search_depth,
                        "api_key": st.session_state.get("llm_api_key", ""),
                        "provider": st.session_state.get("llm_provider", "local")
                    }
                    
                    chat_res = requests.post(f"{API_HOST}/chat", json=chat_payload, timeout=35)
                    
                    if chat_res.status_code == 200:
                        data = chat_res.json()
                        answer_text = data.get("answer", "")
                        sources = data.get("sources", [])
                        
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
                                    
                        st.markdown(
                            """<div class="gemini-action-row">
                              <span class="gemini-action-btn">👍</span>
                              <span class="gemini-action-btn">👎</span>
                              <span class="gemini-action-btn">🔄</span>
                              <span class="gemini-action-btn">📋</span>
                              <span class="gemini-action-btn">⋯</span>
                            </div>""",
                            unsafe_allow_html=True
                        )

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

    # Centered Gemini Disclaimer below chat input
    st.markdown('<div class="gemini-disclaimer-text">Gemini is AI and can make mistakes. Verify important info.</div>', unsafe_allow_html=True)


# ====================================================
# VIEW 2: NOTEBOOKS & DOCUMENT INGESTION
# ====================================================
elif st.session_state["active_view"] == "library":
    st.subheader("📚 Notebooks & Document Ingestion")
    st.caption("Upload files to generate vector embeddings in ChromaDB and assign custom topic icon symbols.")
    
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
        if st.button("🔄 Resync Library", use_container_width=True):
            if api_healthy:
                try:
                    requests.post(f"{API_HOST}/resync", timeout=5)
                except Exception:
                    pass
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.subheader(f"📑 Currently Indexed Notebooks ({len(indexed_docs)})")

    if not indexed_docs:
        st.info("No documents indexed yet. Upload your first file above to get started!")
    else:
        for doc in indexed_docs:
            src_path = doc.get("source_id", "Unknown")
            fname = doc.get("filename") or os.path.basename(src_path)
            ftype = doc.get("source_type", "txt").upper()
            
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
            
            col_card, col_del = st.columns([4, 1.2])
            with col_card:
                st.markdown(
                    f"""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                      <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="font-size: 1.5rem; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: {meta['gradient']}; border-radius: 10px; border: 1px solid {meta['border']};">
                          {meta['symbol']}
                        </div>
                        <div>
                          <div style="font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <span>{fname}</span>
                            <span style="font-size: 0.70rem; padding: 2px 7px; border-radius: 9999px; background: {meta['bg']}; color: {meta['color']}; border: 1px solid {meta['border']}; font-weight: 600;">
                              {meta['badge']}
                            </span>
                          </div>
                          <div style="font-size: 0.76rem; color: #64748B; margin-top: 3px;">
                            Format: <strong>{ftype}</strong> {size_str} &bull; SHA: <code>{fhash}...</code>
                          </div>
                        </div>
                      </div>
                      <div>
                        <span style="background: rgba(37, 99, 235, 0.1); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 600;">
                          Active
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
# VIEW 3: CONFIGURATION, AI ENGINE & SETTINGS
# ====================================================
elif st.session_state["active_view"] == "settings":
    st.subheader("⚙️ Gemini Engine Configuration")
    st.caption("Configure AI providers, search precision, and mobile home screen access.")
    
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
    st.subheader("📱 Install on Mobile Device")
    st.caption("Scan this QR code with your iPhone or Android camera to open and install the app on your home screen:")
    
    col_qr, col_qr_info = st.columns([1, 2])
    with col_qr:
        qr_file = os.path.join(PROJECT_ROOT, "mobile_qr.png")
        if os.path.exists(qr_file):
            st.image(qr_file, width=180)
    with col_qr_info:
        st.markdown("**Mobile Network Link:**")
        st.code("http://192.168.1.53:8501", language="text")
        st.caption("Ensure your phone is connected to the same Wi-Fi network.")
        st.markdown("""
        * **iPhone (Safari)**: Tap Share (box with arrow $\\uparrow$) ➔ *Add to Home Screen*.
        * **Android (Chrome)**: Tap Menu (⋮) ➔ *Install app* or *Add to Home screen*.
        """)

    st.markdown("---")
    st.subheader("🔌 System Diagnostics")
    st.markdown(f"- **FastAPI Backend:** `{API_HOST}` ({'Online 🟢' if api_healthy else 'Offline 🔴'})")
    st.markdown(f"- **Agent Identity:** `Google Gemini Smart Knowledge Base`")
    st.markdown(f"- **Natural Language Engine:** `{provider_format[st.session_state['llm_provider']]}`")
    st.markdown(f"- **Embedding Model:** `all-MiniLM-L6-v2` (SentenceTransformers 384-d)")
    st.markdown(f"- **Indexed Documents:** `{len(indexed_docs)}`")
    st.markdown(f"- **Vector Database:** `ChromaDB Persistent (data/chroma_db)`")
    st.markdown(f"- **Metadata Database:** `SQLite (data/metadata.sqlite)`")
