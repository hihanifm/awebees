@echo off
REM Lens Application Launcher for Windows
REM Handles both self-contained (with Python) and Python-required variants

setlocal enabledelayedexpansion

echo [DEBUG] Starting Lens launcher...
echo [DEBUG] Script location: %~dp0

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
echo [DEBUG] SCRIPT_DIR after dp0: !SCRIPT_DIR!

REM Remove trailing backslash if present
if "!SCRIPT_DIR:~-1!"=="\" (
    echo [DEBUG] Removing trailing backslash
    set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
    echo [DEBUG] SCRIPT_DIR after removal: !SCRIPT_DIR!
) else (
    echo [DEBUG] No trailing backslash found
)
echo [DEBUG] Final SCRIPT_DIR: !SCRIPT_DIR!

REM Check if Python directory exists (self-contained variant)
set "PYTHON_PATH=!SCRIPT_DIR!\python\python.exe"
echo [DEBUG] Checking for embedded Python at: !PYTHON_PATH!
if exist "!PYTHON_PATH!" (
    echo [DEBUG] Found embedded Python
    echo Starting Lens (Self-contained with Python)...
    set "PYTHON_EXE=!PYTHON_PATH!"
    set "VARIANT=with-python"
    echo [DEBUG] PYTHON_EXE set to: !PYTHON_EXE!
) else (
    echo [DEBUG] Embedded Python not found, checking system Python
    echo Starting Lens (Requires Python)...
    REM Check for system Python
    where python >nul 2>&1
    if errorlevel 1 (
        echo [DEBUG] System Python not found in PATH
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.x from https://www.python.org/
        pause
        exit /b 1
    )
    echo [DEBUG] System Python found
    set "PYTHON_EXE=python"
    set "VARIANT=requires-python"
    echo [DEBUG] PYTHON_EXE set to: !PYTHON_EXE!
)

REM Change to script directory
echo [DEBUG] Changing to directory: !SCRIPT_DIR!
cd /d "!SCRIPT_DIR!"
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to change directory
    pause
    exit /b 1
)
echo [DEBUG] Current directory: %CD%

REM Activate virtual environment or create it
echo [DEBUG] Checking for venv at: %CD%\venv\Scripts\activate.bat
if exist "venv\Scripts\activate.bat" (
    echo [DEBUG] Virtual environment exists, activating...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to activate venv
        pause
        exit /b 1
    )
    echo [DEBUG] Virtual environment activated
) else (
    echo [DEBUG] Virtual environment not found, creating...
    echo Creating virtual environment...
    echo [DEBUG] Running: "!PYTHON_EXE!" -m venv venv
    "!PYTHON_EXE!" -m venv venv
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to create virtual environment
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [DEBUG] Virtual environment created, activating...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to activate new venv
        pause
        exit /b 1
    )
    echo [DEBUG] Installing dependencies...
    echo Installing dependencies...
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to upgrade pip
        pause
        exit /b 1
    )
    python -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to install dependencies
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo [DEBUG] Dependencies installed successfully
)

REM Set environment variable for frontend serving
echo [DEBUG] Setting SERVE_FRONTEND=true
set SERVE_FRONTEND=true

REM Start backend
echo [DEBUG] Starting backend...
echo Starting Lens backend on http://localhost:34001...
echo [DEBUG] Changing to backend directory: !SCRIPT_DIR!\backend
cd /d "!SCRIPT_DIR!\backend"
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to change to backend directory
    pause
    exit /b 1
)
echo [DEBUG] Backend directory: %CD%
echo [DEBUG] Starting uvicorn with: python -m uvicorn app.main:app --host 0.0.0.0 --port 34001
start "Lens Backend" /min python -m uvicorn app.main:app --host 0.0.0.0 --port 34001
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to start backend
    pause
    exit /b 1
)
echo [DEBUG] Backend process started

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:34001

echo.
echo Lens is starting...
echo Backend: http://localhost:34001
echo.
echo Press any key to close this window (Lens will continue running in background)
pause >nul

