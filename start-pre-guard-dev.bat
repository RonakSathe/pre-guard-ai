```bat
@echo off
title PRE-GUARD AI - DEVELOPMENT MODE

echo.
echo ============================================================
echo                 PRE-GUARD AI
echo                  DEVELOPMENT MODE
echo ============================================================
echo.

cd /d R:\pre-guard-ai\pre-guard-ai

echo [1/2] Checking Render API...
echo.
echo Backend: https://pre-guard-ai.onrender.com
echo.

echo [2/2] Starting Chrome Extension Development Server...
echo.

cd /d R:\pre-guard-ai\pre-guard-ai\extension-v2\pre-guard-extension

start "PRE-GUARD Extension - DEV" cmd /k "pnpm dev"

echo.
echo ============================================================
echo          PRE-GUARD AI DEVELOPMENT MODE STARTED
echo ============================================================
echo.
echo Backend:    Render Cloud API
echo Extension:  Plasmo Development Server
echo Mode:       Development
echo.
echo Hot Reload: Enabled
echo Local API:  Not Required
echo.
echo Keep the extension terminal open.
echo ============================================================
echo.

pause
```