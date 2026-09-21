@echo off
setlocal enabledelayedexpansion

echo === BurnInGuard AI 2.0 - Dependency Installer ===

cd frontend
echo [1/4] Installing frontend dependencies...
npm install --prefer-offline --no-audit
if errorlevel 1 (
    echo Frontend dependency installation failed.
    exit /b 1
)

cd ..
if not exist .venv (
    echo [2/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Virtual environment creation failed.
        exit /b 1
    )
)

echo [3/4] Activating virtual environment and installing backend dependencies...
call .venv\Scripts\activate
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo Backend dependency installation failed.
    exit /b 1
)

echo [4/4] Installing model training dependencies...
cd ..\model-training
pip install -r requirements.txt
if errorlevel 1 (
    echo Model training dependency installation failed.
    exit /b 1
)

deactivate
echo Dependencies installed successfully.
exit /b 0
