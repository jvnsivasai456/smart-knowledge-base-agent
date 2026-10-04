@echo off
title Smart Knowledge Base App Launcher
cd /d "%~dp0"

echo =======================================================
echo        Smart Knowledge Base Agent - App Launcher
echo =======================================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Creating venv...
    python -m venv venv
    call venv\Scripts\activate
    echo [*] Installing dependencies (this may take a couple minutes on first run)...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo [*] Starting FastAPI Backend (Port 8000)...
start /b "" venv\Scripts\python.exe main.py

echo [*] Starting Streamlit App (Port 8501)...
timeout /t 3 /nobreak >nul

:: Open browser in standalone app window mode (Edge or Chrome if available, fallback to default browser)
start /b "" venv\Scripts\streamlit.exe run src/ui/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

timeout /t 2 /nobreak >nul

:: Launch browser in dedicated window mode
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8501
) else if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=http://localhost:8501
) else (
    start http://localhost:8501
)

echo.
echo =======================================================
echo    App is running!
echo    Local URL:    http://localhost:8501
echo    Network URL:  http://10.22.230.15:8501
echo    Backend Docs: http://localhost:8000/docs
echo =======================================================
echo.
echo Press any key to stop all background services and exit...
pause >nul

echo [*] Stopping services...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM streamlit.exe /T 2>nul
echo Done.
