```bat
@echo off
title PRE-GUARD AI

echo.
echo ============================================================
echo                  PRE-GUARD AI
echo ============================================================
echo.

cd /d R:\pre-guard-ai\pre-guard-ai

echo [1/1] Starting Chrome extension...
cd /d R:\pre-guard-ai\pre-guard-ai\extension-v2\pre-guard-extension

start "PRE-GUARD Extension" cmd /k "pnpm dev"

echo.
echo ============================================================
echo              PRE-GUARD AI STARTED
echo ============================================================
echo.
echo Backend:    https://pre-guard-ai.onrender.com
echo Extension:  Plasmo development server
echo.
echo Your API is hosted on Render.
echo No local API server is required.
echo ============================================================
echo.

pause
```