# Smart knowledge Base Agent

A modular, smart document ingestion and retrieval system using Python, FastAPI, Streamlit, and ChromaDB.

## Features
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

### 1. Locally (Development)
```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# Run API
python main.py

# Run UI (in a separate terminal)
streamlit run src/ui/app.py
```

### 2. Docker Compose
```bash
docker-compose up --build
```
- API will be at `http://localhost:8000`
- UI will be at `http://localhost:8501`

### 3. Generic Linux Server / Cloud VM
You can deploy this via Docker on any cloud VM:
```bash
git clone <your-repo-url>
cd smart_kb
docker-compose up -d --build
```
Ensure ports `8000` and `8501` are open in your server's firewall. 
The `/health` endpoint is available at `http://<server-ip>:8000/health` for load balancers and container orchestrators.
