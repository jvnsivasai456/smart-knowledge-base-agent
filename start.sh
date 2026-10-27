#!/bin/sh
# Start the FastAPI backend in background
python main.py &

# Wait for backend initialization
sleep 2

# Start the Streamlit UI in foreground
streamlit run src/ui/app.py --server.address 0.0.0.0 --server.port 8501
