import sys
import urllib.request
import urllib.error
import uvicorn
from src.config import settings

def is_backend_already_running(host: str, port: int) -> bool:
    """Check if the backend is already active and healthy."""
    target_host = "127.0.0.1" if host in ("0.0.0.0", "localhost") else host
    url = f"http://{target_host}:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

if __name__ == "__main__":
    if is_backend_already_running(settings.host, settings.port):
        print("=" * 60)
        print("  [OK] Smart Knowledge Base Agent Backend is ALREADY running!")
        print(f"  [OK] URL: http://{settings.host}:{settings.port}")
        print("  [OK] Status: Healthy and ready to serve requests.")
        print("=" * 60)
        sys.exit(0)

    try:
        print(f"[*] Starting Smart Knowledge Base Backend on http://{settings.host}:{settings.port} ...")
        uvicorn.run("src.api.main:app", host=settings.host, port=settings.port, reload=False)
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"[*] Notice: Port {settings.port} is already in use by an active service.")
            sys.exit(0)
        else:
            raise e
