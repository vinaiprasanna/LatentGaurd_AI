@echo off
setlocal enabledelayedexpansion

if not exist .venv (
    echo Error: Virtual environment not found. Run install-dependencies.bat first.
    exit /b 1
)

call .venv\Scripts\activate
cd backend
echo Starting BurnInGuard AI 2.0 backend on port 8000...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
