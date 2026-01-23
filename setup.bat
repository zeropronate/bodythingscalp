@echo off
REM Quick start script for Blood Report Analyzer (Windows)
REM Run this after copying project to new PC with Ollama installed

setlocal enabledelayedexpansion

echo ================================
echo Blood Report Analyzer - Quick Start
echo ================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1 || (
    echo X Python not found. Please install Python 3.12+
    exit /b 1
)

REM Check Ollama
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1 || (
    echo X Ollama not running on localhost:11434
    echo   Please start Ollama service
    exit /b 1
)

echo O Ollama is running

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ================================
echo Setup Complete! ✅
echo ================================
echo.
echo Start the application:
echo.
echo Command Prompt 1 (Backend API):
echo   .venv\Scripts\activate.bat
echo   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Command Prompt 2 (Frontend UI):
echo   .venv\Scripts\activate.bat
echo   streamlit run frontend/app.py
echo.
echo Then open browser to:
echo   http://localhost:8501
echo.
echo Optional: Copy .env.example to .env to customize settings
echo.
pause

