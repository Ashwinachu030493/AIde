@echo off
echo Starting AIde Server...
cd server
if not exist "..\venv" (
    echo Virtual environment not found in ..\venv. Please install dependencies first.
    pause
    exit /b 1
)
call ..\venv\Scripts\activate.bat
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
pause
