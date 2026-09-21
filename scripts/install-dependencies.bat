@echo off

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo === LatentGuard AI - Dependency Installer ===
echo.

REM Check if frontend dependencies already exist
if exist "%PROJECT_ROOT%\frontend\node_modules\" (
    echo [1/4] Frontend dependencies already installed. Skipping.
) else (
    pushd "%PROJECT_ROOT%\frontend"
    echo [1/4] Installing frontend dependencies...
    npm install --prefer-offline --no-audit
    if errorlevel 1 (
        echo Frontend dependency installation failed.
        popd
        exit /b 1
    )
    popd
)

REM Check if virtual environment exists
if exist "%PROJECT_ROOT%\.venv\" (
    echo [2/4] Virtual environment already exists. Skipping.
) else (
    echo [2/4] Creating virtual environment...
    python -m venv "%PROJECT_ROOT%\.venv"
    if errorlevel 1 (
        echo Virtual environment creation failed.
        exit /b 1
    )
)

REM Check if backend is already installed
if exist "%PROJECT_ROOT%\backend\env_installed.txt" (
    echo [3/4] Backend dependencies already installed. Skipping.
) else (
    echo [3/4] Installing backend dependencies...
    pushd "%PROJECT_ROOT%\backend"
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Backend dependency installation failed.
        popd
        exit /b 1
    )
    echo ready> "%PROJECT_ROOT%\backend\env_installed.txt"
    popd
)

REM Check if model-training is already installed
if exist "%PROJECT_ROOT%\model-training\env_installed.txt" (
    echo [4/4] Model training dependencies already installed. Skipping.
) else (
    echo [4/4] Installing model training dependencies...
    pushd "%PROJECT_ROOT%\model-training"
    call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Model training dependency installation failed.
        popd
        exit /b 1
    )
    echo ready> "%PROJECT_ROOT%\model-training\env_installed.txt"
    popd
)

echo.
echo Dependencies installed successfully.
