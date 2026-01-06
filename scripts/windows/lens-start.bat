@echo off
REM Lens Application Launcher for Windows
REM Handles both self-contained (with Python) and Python-required variants

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if Python directory exists (self-contained variant)
if exist "%SCRIPT_DIR%\python\python.exe" (
    echo Starting Lens (Self-contained with Python)...
    set "PYTHON_EXE=%SCRIPT_DIR%\python\python.exe"
    set "VARIANT=with-python"
) else (
    echo Starting Lens (Requires Python)...
    REM Check for system Python
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.x from https://www.python.org/
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
    set "VARIANT=requires-python"
)

REM Change to script directory
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment or create it
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Set environment variable for frontend serving
set SERVE_FRONTEND=true

REM Start backend
echo Starting Lens backend on http://localhost:34001...
cd /d "%SCRIPT_DIR%\backend"
start "Lens Backend" /min python -m uvicorn app.main:app --host 0.0.0.0 --port 34001

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

