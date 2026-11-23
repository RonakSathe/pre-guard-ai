
@echo off
title PRE-GUARD AI - DEV Launcher

cd /d R:\pre-guard-ai\pre-guard-ai

echo.
echo ============================================
echo        PRE-GUARD AI - DEV STARTUP
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment Python not found!
    pause
    exit /b 1
)

echo [1/2] Starting FastAPI Backend...
start "PRE-GUARD Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn api.main:app --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Streamlit Dashboard...
start "PRE-GUARD Dashboard" cmd /k ".venv\Scripts\python.exe -m streamlit run dashboard/app.py

echo.
echo ============================================
echo        PRE-GUARD AI STARTED
echo ============================================
echo.
echo Backend  : http://127.0.0.1:8000
echo API Docs : http://127.0.0.1:8000/docs
echo Dashboard: http://localhost:8501
echo.
pause
