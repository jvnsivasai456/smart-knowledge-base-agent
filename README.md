# Smart Knowledge Base Agent

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=jvnsivasai456/smart-knowledge-base-agent&branch=main&mainModule=src/ui/app.py)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jvnsivasai456/smart-knowledge-base-agent)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65.0-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)

A modular, smart document ingestion and retrieval system using Python, FastAPI, Streamlit, and ChromaDB.

> **24/7 Cloud Deployment**: Run this app 24/7 in the cloud without needing your personal laptop turned on by clicking the **Deploy to Streamlit Cloud** badge above.

## Features
- **Hybrid Retrieval**: Combines Okapi BM25 keyword matching and dense vector embeddings fused via Reciprocal Rank Fusion ($k=60$) with a 62% confidence gate.
- **Multi-Format Ingestion**: Supports PDF, DOCX, TXT, and HTML.
- **Smart Chunking**: Overlapping context-aware chunks.
- **Vector Search**: Semantic search powered by `sentence-transformers` and `ChromaDB`.
- **Continuous Background Updates**: `APScheduler` scans for new/modified/deleted files and updates only what's changed without full rebuilds.

## Architecture
- `src/api`: FastAPI server exposing `/upload` and `/search`. Runs the background APScheduler.
- `src/ui`: Streamlit frontend for interacting with the API.
- `src/ingestion`: Document parsing and text extraction.
- `src/processing`: Text cleaning and overlapping character chunking.
- `src/embedding`: Sentence embedding and Vector/SQLite database orchestration.
- `src/update_engine`: File hashing, diff calculation, and update pipeline.

## Environment Variables
Create a `.env` file based on `.env.example`:
- `HOST`: API host (default `0.0.0.0`)
- `PORT`: API port (default `8000`)
- `API_HOST`: Used by UI to connect to API (default `http://127.0.0.1:8000`)
- `DATA_DIR`: Root folder for persistence
- `EMBEDDING_MODEL_NAME`: HuggingFace model for embeddings (default `all-MiniLM-L6-v2`)
- `SCHEDULER_INTERVAL_MINUTES`: Frequency of file scans (default `60`)

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

### 3. Docker Compose
```bash
git clone https://github.com/jvnsivasai456/smart-knowledge-base-agent.git
cd smart-knowledge-base-agent
docker-compose up --build
```
- API will be at `http://localhost:8000`
- UI will be at `http://localhost:8501`

### 4. Generic Linux Server / Cloud VM
```bash
git clone https://github.com/jvnsivasai456/smart-knowledge-base-agent.git
cd smart-knowledge-base-agent
docker-compose up -d --build
```
Ensure ports `8000` and `8501` are open in your server's firewall. 
The `/health` endpoint is available at `http://<server-ip>:8000/health` for load balancers and container orchestrators.
