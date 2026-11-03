# Smart Knowledge Base Agent

[![Live Web App](https://img.shields.io/badge/Live_Web_App-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://smart-knowledge-base-agent.streamlit.app)
[![Open in GitHub Codespaces](https://img.shields.io/badge/Open_in-Codespaces-blue?style=for-the-badge&logo=github&logoColor=white)](https://codespaces.new/jvnsivasai456/smart-knowledge-base-agent)
[![Download Report](https://img.shields.io/badge/Project_Report-.docx-2B579A?style=for-the-badge&logo=microsoftword&logoColor=white)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/docs/SMART_KNOWLEDGE_BASE_AGENT_REPORT_44110216.docx)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/jvnsivasai456/smart-knowledge-base-agent)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65.0-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)

A modular, smart document ingestion and retrieval system using Python, FastAPI, Streamlit, and ChromaDB.

---

## 🔗 Quick Links & Access Directory

| Resource | Direct Link | Description |
| :--- | :--- | :--- |
| 🌐 **24/7 Live Cloud Web App** | [smart-knowledge-base-agent.streamlit.app](https://smart-knowledge-base-agent.streamlit.app) | Public live deployment on Streamlit Cloud (accessible 24/7 worldwide) |
| ⚡ **One-Click Cloud Codespaces** | [Launch in GitHub Codespaces](https://codespaces.new/jvnsivasai456/smart-knowledge-base-agent) | Pre-configured Linux cloud container running both Backend & UI |
| 💻 **GitHub Source Repository** | [github.com/jvnsivasai456/smart-knowledge-base-agent](https://github.com/jvnsivasai456/smart-knowledge-base-agent) | Official source repository on GitHub |
| 📦 **Download Source Code ZIP** | [Download project .zip](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/smart-knowledge-base-agent.zip) | Complete source bundle archive |
| 📄 **Official Academic Project Report (.docx)** | [Download Word Report (.docx)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/docs/SMART_KNOWLEDGE_BASE_AGENT_REPORT_44110216.docx) | Formal academic submission report for Sathyabama University |
| 📝 **Online Project Report (.md)** | [Read Markdown Report (.md)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/blob/main/docs/SMART_KNOWLEDGE_BASE_AGENT_REPORT_44110216.md) | Formatted report with system architecture & evaluation metrics |
| 📊 **5-Min Team Review Presentation (.pdf)** | [Download 5-Min Slides (.pdf)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/docs/SMART_KB_5MIN_TEAM_REVIEW_PRESENTATION.pdf) | [Read Markdown](https://github.com/jvnsivasai456/smart-knowledge-base-agent/blob/main/docs/SMART_KB_5MIN_TEAM_REVIEW_PRESENTATION.md) | 8-Slide Team Review Slides & Spoken Scripts for Siva Sai, Bhargav & Karthikeya |
| 📈 **10-Min In-Depth Presentation (.pdf)** | [Download 10-Min Slides (.pdf)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/docs/SMART_KB_10MIN_TEAM_REVIEW_PRESENTATION.pdf) | [Read Markdown](https://github.com/jvnsivasai456/smart-knowledge-base-agent/blob/main/docs/SMART_KB_10MIN_TEAM_REVIEW_PRESENTATION.md) | 12-Slide Comprehensive Technical Presentation & Viva Walkthrough |
| 📘 **Review & Viva Preparation Handbook (.pdf)** | [Download Handbook (.pdf)](https://github.com/jvnsivasai456/smart-knowledge-base-agent/raw/main/docs/SMART_KNOWLEDGE_BASE_AGENT_REVIEW_HANDBOOK.pdf) | [Read Markdown](https://github.com/jvnsivasai456/smart-knowledge-base-agent/blob/main/docs/SMART_KNOWLEDGE_BASE_AGENT_REVIEW_HANDBOOK.md) | Quick-reference Viva cheat sheet, architecture FAQ & live demo sequence |
| 🖥️ **Local Web Interface** | `http://localhost:8501` | Local Streamlit UI when running `run_app.bat` |
| 🚀 **FastAPI Backend Service** | `http://localhost:8000/health` | REST API health check endpoint |

---

### 🎓 Academic Project Information
* **Students / Authors:** 
  - `GOLLA JAYA VENKATA NAGA SIVA SAI (44110216)`
  - `GUNDA BHARGAV (44110216)`
  - `GANTA KARTHIKEYA (44110202)`
* **Degree & Department:** Bachelor of Engineering (B.E.), Department of Computer Science and Engineering
* **Institution:** Sathyabama Institute of Science and Technology (Deemed to be University), Chennai
* **Internal Guide:** `Ms. M. DEVIPRIYA`
* **Head of the Department:** `Dr. L. LAKSHMANAN, M.E., Ph.D.`
* **Academic Session:** July 2026 – November 2026
* **Project Title:** Smart Knowledge Base Agent

---

## Features
- **Hybrid Retrieval**: Combines Okapi BM25 keyword matching and dense vector embeddings fused via Reciprocal Rank Fusion ($k=60$) with a 62% confidence gate.
- **Multi-Format Ingestion**: Supports PDF, DOCX, TXT, and HTML.
- **Smart Chunking**: Overlapping context-aware chunks (800 chars / 120 token overlap).
- **Vector Search**: Semantic search powered by `sentence-transformers` (`all-MiniLM-L6-v2`) and `ChromaDB`.
- **Continuous Background Updates**: `APScheduler` scans for new/modified/deleted files using SHA-256 diffing and updates only what's changed without full rebuilds.
- **Multi-Model Answer Engine**: Supports built-in offline Local NLG as well as Google Gemini, Anthropic Claude (3.5 Sonnet), Groq (Llama-3.1), OpenAI (GPT-4o), and Local Ollama.

---

## Architecture
- `src/api`: FastAPI server exposing `/upload`, `/search`, `/chat`, and `/documents`. Runs the background APScheduler.
- `src/ui`: Streamlit frontend for interacting with the API and in-process resilient chat.
- `src/ingestion`: Document parsing and text extraction (PDF, DOCX, TXT, HTML).
- `src/processing`: Text cleaning and overlapping character chunking.
- `src/embedding`: Sentence embedding and Vector/SQLite database orchestration.
- `src/update_engine`: File hashing, diff calculation, and update pipeline.

---

## Environment Variables
Create a `.env` file based on `.env.example`:
- `HOST`: API host (default `0.0.0.0`)
- `PORT`: API port (default `8000`)
- `API_HOST`: Used by UI to connect to API (default `http://127.0.0.1:8000`)
- `DATA_DIR`: Root folder for persistence
- `EMBEDDING_MODEL_NAME`: HuggingFace model for embeddings (default `all-MiniLM-L6-v2`)
- `SCHEDULER_INTERVAL_MINUTES`: Frequency of file scans (default `60`)

---

## How to Run

### 1. In GitHub (1-Click Cloud Execution via Codespaces)
Click the **[Open in GitHub Codespaces](https://codespaces.new/jvnsivasai456/smart-knowledge-base-agent)** button to launch a fully configured cloud container. 
- Python 3.11, all dependencies, and models are prepared automatically.
- Both the **FastAPI Backend (port 8000)** and **Streamlit UI (port 8501)** launch automatically.
- Accessible directly from your browser with port forwarding.

### 2. Locally from Git
```bash
# Clone the repository
git clone https://github.com/jvnsivasai456/smart-knowledge-base-agent.git
cd smart-knowledge-base-agent

# Create virtual environment & install dependencies
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# Start Backend API (Port 8000)
python main.py

# Start UI (Port 8501) in a separate terminal
streamlit run src/ui/app.py
```

### 3. Quick Run on Windows
Double-click `run_app.bat` to launch both backend and UI automatically in your default browser at `http://localhost:8501`.

### 4. Docker Compose
```bash
git clone https://github.com/jvnsivasai456/smart-knowledge-base-agent.git
cd smart-knowledge-base-agent
docker-compose up --build
```
- API will be at `http://localhost:8000`
- UI will be at `http://localhost:8501`

### 5. Generic Linux Server / Cloud VM
```bash
git clone https://github.com/jvnsivasai456/smart-knowledge-base-agent.git
cd smart-knowledge-base-agent
docker-compose up -d --build
```
Ensure ports `8000` and `8501` are open in your server's firewall. 
The `/health` endpoint is available at `http://<server-ip>:8000/health` for load balancers and container orchestrators.
