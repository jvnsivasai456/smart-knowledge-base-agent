@echo off
title Smart Knowledge Base Agent
cd /d "%~dp0"

echo =======================================================
echo        Smart Knowledge Base Agent - App Launcher
echo =======================================================
echo.

:: 1. Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Creating venv...
    python -m venv venv
    call venv\Scripts\activate
    echo [*] Installing dependencies (this may take a couple minutes on first run)...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: 2. Check if FastAPI backend (Port 8000) is already running
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [*] Starting FastAPI Backend on Port 8000...
    start /b "" venv\Scripts\python.exe main.py
    timeout /t 2 /nobreak >nul
) else (
    echo [OK] FastAPI Backend is already active on Port 8000.
)

:: 3. Check if Streamlit UI (Port 8501) is already running
netstat -ano | findstr ":8501 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [*] Starting Streamlit App on Port 8501...
    start /b "" venv\Scripts\streamlit.exe run src/ui/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Streamlit UI is already active on Port 8501.
)

:: 4. Check if Cloudflare Tunnel is running for Mobile Network (4G/5G) Access
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | findstr /i "cloudflared.exe" >nul 2>&1
if errorlevel 1 (
    echo [*] Starting Mobile Network Tunnel (4G/5G Worldwide Access)...
    start /b "" venv\Scripts\python.exe start_tunnel.py
    timeout /t 4 /nobreak >nul
) else (
    echo [OK] Mobile Network Tunnel is already active.
)

:: 5. Launch browser in standalone app window mode
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
echo    Local URL:      http://localhost:8501
if exist "tunnel_url.txt" (
    set /p TUNNEL_LINK=<tunnel_url.txt
    call echo    Mobile Network: %%TUNNEL_LINK%% (4G/5G Anywhere)
)
echo    Wi-Fi LAN:      http://192.168.1.53:8501
echo    Backend Docs:   http://localhost:8000/docs
echo =======================================================
echo.
echo Press any key to stop application services and exit...
pause >nul

echo [*] Stopping services safely on ports 8000 and 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
taskkill /F /IM cloudflared.exe 2>nul
echo Done.
