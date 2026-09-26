@echo off

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if not exist "%PROJECT_ROOT%\frontend\node_modules\" (
    echo Error: Frontend dependencies not found. Run install-dependencies.bat first.
    exit /b 1
)

pushd "%PROJECT_ROOT%\frontend"
echo Starting LatentGuard AI frontend on port 3000...
npm run dev
