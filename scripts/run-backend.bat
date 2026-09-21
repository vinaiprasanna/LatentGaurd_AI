call .venv\Scripts\activate
if errorlevel 1 (
    echo Virtual environment activation failed.
    exit /b 1
)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
