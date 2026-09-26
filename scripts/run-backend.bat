@echo off

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if not exist "%PROJECT_ROOT%\.venv\" (
    echo Error: Virtual environment not found. Run install-dependencies.bat first.
    exit /b 1
)

pushd "%PROJECT_ROOT%\backend"
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
echo Starting LatentGuard AI backend on port 8000...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
