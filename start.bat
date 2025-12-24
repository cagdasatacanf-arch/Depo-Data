@echo off
REM Depo API - Quick Start Script for Windows

echo ========================================
echo Depo - Historical Data API
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Installing/Updating dependencies...
pip install -r requirements.txt
echo.

echo Starting Depo API Server...
echo.
echo API will be available at:
echo - Main API: http://localhost:8000
echo - Interactive Docs: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
