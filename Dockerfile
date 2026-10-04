FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl needed for healthcheck, build-essential for some pip packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download default embedding model to avoid startup delays
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application source
COPY . .
RUN chmod +x start.sh || true

# Expose API and Streamlit UI ports
EXPOSE 8000 8501

# Default command runs the API
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
