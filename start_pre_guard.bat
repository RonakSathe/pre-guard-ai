@echo off
title PRE-GUARD AI

echo.
echo ============================================================
echo                  PRE-GUARD AI
echo ============================================================
echo.

cd /d R:\pre-guard-ai\pre-guard-ai

echo [1/2] Starting AI API server...
start "PRE-GUARD AI API" cmd /k ".venv\Scripts\activate && python -m uvicorn api.main:app --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Chrome extension...
cd /d R:\pre-guard-ai\pre-guard-ai\extension-v2\pre-guard-extension
start "PRE-GUARD Extension" cmd /k "pnpm dev"

echo.
echo ============================================================
echo              PRE-GUARD AI STARTED
echo ============================================================
echo.
echo API:       http://127.0.0.1:8000
echo Extension: Plasmo development server
echo.
echo Keep both terminal windows open.
echo ============================================================
echo.

pause