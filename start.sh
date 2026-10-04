#!/bin/sh
# Start the FastAPI backend in background
uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Start the Streamlit UI in foreground
streamlit run src/ui/app.py --server.address 0.0.0.0 --server.port 8501
