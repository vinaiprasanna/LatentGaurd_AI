@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo === BurnInGuard AI 2.0 - Dependency Installer ===
echo.

pushd "%PROJECT_ROOT%\frontend"
echo [1/4] Installing frontend dependencies...
npm install --prefer-offline --no-audit
if errorlevel 1 (
    echo Frontend dependency installation failed.
    popd
    exit /b 1
)
popd

if not exist "%PROJECT_ROOT%\.venv\" (
    echo [2/4] Creating virtual environment...
    python -m venv "%PROJECT_ROOT%\.venv"
    if errorlevel 1 (
        echo Virtual environment creation failed.
        exit /b 1
    )
)

echo [3/4] Installing backend dependencies...
pushd "%PROJECT_ROOT%\backend"
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
pip install -r requirements.txt
if errorlevel 1 (
    echo Backend dependency installation failed.
    popd
    exit /b 1
)
popd

echo [4/4] Installing model training dependencies...
pushd "%PROJECT_ROOT%\model-training"
pip install -r requirements.txt
if errorlevel 1 (
    echo Model training dependency installation failed.
    popd
    exit /b 1
)
popd

echo.
echo Dependencies installed successfully.
endlocal
