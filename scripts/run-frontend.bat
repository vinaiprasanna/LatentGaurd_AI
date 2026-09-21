@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

pushd "%PROJECT_ROOT%\frontend"
echo Starting BurnInGuard AI 2.0 frontend on port 3000...
npm run dev
