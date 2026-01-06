@echo off
REM Lens Application Launcher for Windows
REM Handles both self-contained (with Python) and Python-required variants

setlocal enabledelayedexpansion

echo [DEBUG] Starting Lens launcher...

REM Change to script directory immediately using %~dp0
REM This avoids any issues with storing paths containing special characters
cd /d "%~dp0"
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to change to script directory
    echo ERROR: Cannot access installation directory
    pause
    exit /b 1
)
echo [DEBUG] Changed to directory: %CD%

echo [DEBUG] Checking for embedded Python at: python\python.exe
if exist "python\python.exe" (
    echo [DEBUG] Found embedded Python
    echo Starting Lens (Self-contained with Python)...
    set "PYTHON_EXE=python\python.exe"
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

REM We're already in script directory from Python check above
echo [DEBUG] Current directory: %CD%

REM Activate virtual environment or create it
echo [DEBUG] Checking for venv
if exist "venv\Scripts\activate.bat" (
    echo [DEBUG] Virtual environment exists, activating...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to activate virtual environment
        echo ERROR: Failed to activate virtual environment
        pause
        exit /b 1
    )
    echo [DEBUG] Virtual environment activated
) else (
    echo [DEBUG] Creating virtual environment...
    echo Creating virtual environment...
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
        echo [DEBUG] ERROR: Failed to activate newly created virtual environment
        echo ERROR: Failed to activate newly created virtual environment
        pause
        exit /b 1
    )
    echo [DEBUG] Virtual environment activated
    echo [DEBUG] Installing dependencies...
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [DEBUG] ERROR: Failed to upgrade pip
        echo ERROR: Failed to upgrade pip
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
    echo [DEBUG] Dependencies installed
)

REM Set environment variable for frontend serving
echo [DEBUG] Setting SERVE_FRONTEND=true
set SERVE_FRONTEND=true

REM Start backend
echo [DEBUG] Changing to backend directory
cd /d backend
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to change to backend directory
    echo ERROR: Failed to change to backend directory
    pause
    exit /b 1
)
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Starting backend server
echo Starting Lens backend on http://localhost:34001...
start "Lens Backend" /min python -m uvicorn app.main:app --host 0.0.0.0 --port 34001
if errorlevel 1 (
    echo [DEBUG] ERROR: Failed to start backend
    echo ERROR: Failed to start backend
    pause
    exit /b 1
)
echo [DEBUG] Backend started

REM Wait a moment for server to start
echo [DEBUG] Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul
echo [DEBUG] Wait complete

REM Open browser
echo [DEBUG] Opening browser to http://localhost:34001
start http://localhost:34001

echo.
echo Lens is starting...
echo Backend: http://localhost:34001
echo.
echo Press any key to close this window (Lens will continue running in background)
pause >nul

