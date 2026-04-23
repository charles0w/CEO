@echo off
echo.
echo  ================================
echo   CEO - Personal AI Assistant
echo  ================================
echo.
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from python.org
    pause & exit /b 1
)

if not exist ".venv" (
    echo [Setup] Creating virtual environment...
    python -m venv .venv
    echo [Setup] Installing dependencies ^(first run, takes a few minutes^)...
    .venv\Scripts\pip install --upgrade pip -q
    .venv\Scripts\pip install -r requirements.txt -q
    echo [Setup] Done.
    echo.
)

echo [CEO] Server starting on http://0.0.0.0:8000
echo [CEO] Local:   http://localhost:8000
echo [CEO] Network: http://<your-ip>:8000
echo [CEO] Press Ctrl+C to stop.
echo.

.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
