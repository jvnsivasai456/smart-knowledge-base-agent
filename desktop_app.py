import sys
import os
import time
import subprocess
import urllib.request
import webview

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
STREAMLIT_EXE = os.path.join(PROJECT_DIR, "venv", "Scripts", "streamlit.exe")

def is_server_ready(url, timeout=1):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status in (200, 404)
    except Exception:
        return False

def start_services():
    processes = []
    
    # Check if backend (port 8000) is running
    if not is_server_ready("http://localhost:8000/health"):
        print("[*] Starting backend API on port 8000...")
        p_api = subprocess.Popen(
            [VENV_PYTHON, "main.py"],
            cwd=PROJECT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        processes.append(p_api)
        
    # Check if Streamlit (port 8501) is running
    if not is_server_ready("http://localhost:8501"):
        print("[*] Starting UI on port 8501...")
        p_ui = subprocess.Popen(
            [
                STREAMLIT_EXE, "run", "src/ui/app.py",
                "--server.address", "0.0.0.0",
                "--server.port", "8501",
                "--server.headless", "true"
            ],
            cwd=PROJECT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        processes.append(p_ui)
        
    # Wait until Streamlit is responsive
    for _ in range(30):
        if is_server_ready("http://localhost:8501"):
            break
        time.sleep(1)
        
    return processes

def main():
    processes = start_services()
    
    # Create native Windows desktop window
    window = webview.create_window(
        title="Smart Knowledge Base",
        url="http://localhost:8501",
        width=1280,
        height=850,
        min_size=(900, 600),
        confirm_close=False,
        text_select=True
    )
    
    # Start the desktop application GUI
    webview.start(debug=False)
    
    # Cleanup when user closes desktop app
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
