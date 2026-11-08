
@echo off
title PRE-GUARD AI - DEVELOPMENT MODE

echo Starting PRE-GUARD AI...

cd /d R:\pre-guard-ai\pre-guard-ai
start "PRE-GUARD API" cmd /k "python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"

cd /d R:\pre-guard-ai\pre-guard-ai\extension-v2\pre-guard-extension
start "PRE-GUARD Extension" cmd /k "pnpm dev"

echo.
echo PRE-GUARD AI DEVELOPMENT STARTED
echo Backend: localhost:8000
echo Extension: Plasmo Dev
pause
