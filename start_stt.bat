@echo off
title Modern Global STT System v2.0
color 0A

echo.
echo ==========================================
echo    Modern Global STT System v2.0
echo ==========================================
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

REM Start the Modern Global STT system
echo Starting Modern Global STT (Qt tray)...
echo Models will load from cache (faster after first run)
echo.
python modern_global_stt.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo ERROR: Failed to start Modern Global STT
    echo ==========================================
    echo.
    echo Possible solutions:
    echo 1. Install Qt dependencies: pip install PySide6
    echo 2. Check dependencies: python modern_global_stt.py --info
    echo 3. Try headless mode: python modern_global_stt.py --headless
    echo.
)

pause
