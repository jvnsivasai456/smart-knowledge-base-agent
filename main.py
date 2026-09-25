import uvicorn
from src.config import settings

if __name__ == "__main__":
    # Binds to the configured host/port, defaulting to 0.0.0.0:8000
    uvicorn.run("src.api.main:app", host=settings.host, port=settings.port, reload=False)
