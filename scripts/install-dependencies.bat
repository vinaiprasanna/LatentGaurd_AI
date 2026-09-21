
@echo off
cd frontend
echo Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo Frontend dependencies installation failed.
    exit /b 1
)
cd ..

echo Creating virtual environment...
if not exist .venv (
    python -m venv .venv
)
if errorlevel 1 (
    echo Virtual environment creation failed.
    exit /b 1
)
echo Virtual environment created.


call .venv\Scripts\activate
if errorlevel 1 (
    echo Virtual environment activation failed.
    exit /b 1
)
echo Virtual environment activated.
cd backend

echo Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Backend dependencies installation failed.
    exit /b 1
)
cd ..
cd model-training

echo Installing model training dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Model training dependencies installation failed.
    exit /b 1
)
cd ..
deactivate
echo Dependencies installed successfully.
exit /b 1
