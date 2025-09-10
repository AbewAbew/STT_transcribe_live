@echo off
title Advanced RealtimeSTT System
color 0A

echo.
echo ========================================
echo    Advanced RealtimeSTT System
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the Global STT (Qt tray)
echo Starting Global STT (Qt tray)...
python start_stt.py

pause
