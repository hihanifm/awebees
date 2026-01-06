@echo off
REM Setup script for Lens - Run this once before starting services
REM This script sets up the Python virtual environment, installs dependencies,
REM and creates .env files from examples

setlocal enabledelayedexpansion

echo Setting up Lens...
echo.

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM ===================================
REM Backend Setup
REM ===================================
echo === Backend Setup ===
cd /d "%PROJECT_ROOT%\backend"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create Python virtual environment
        echo Please ensure Python 3.x is installed and in PATH
        pause
        exit /b 1
    )
    echo Virtual environment created in backend\venv
) else (
    echo Virtual environment already exists in backend\venv
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate Python virtual environment
    pause
    exit /b 1
)

python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed
call deactivate

REM Create .env file from .env.example if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created backend\.env from .env.example
    ) else (
        echo Warning: .env.example not found, creating basic .env file
        (
            echo PORT=5001
            echo HOST=0.0.0.0
            echo FRONTEND_URL=http://localhost:5000
            echo LOG_LEVEL=INFO
        ) > .env
        echo Created basic backend\.env file
    )
) else (
    echo backend\.env already exists, skipping
)

echo.

REM ===================================
REM Frontend Setup
REM ===================================
echo === Frontend Setup ===
cd /d "%PROJECT_ROOT%\frontend"

REM Install npm dependencies
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install Node.js dependencies
        echo Please ensure Node.js and npm are installed and in PATH
        pause
        exit /b 1
    )
    echo Node.js dependencies installed
) else (
    echo Node.js dependencies already installed
)

REM Create .env.local file from .env.example if it doesn't exist
if not exist ".env.local" (
    if exist ".env.example" (
        copy .env.example .env.local >nul
        echo Created frontend\.env.local from .env.example
    ) else (
        echo Warning: .env.example not found, creating basic .env.local file
        (
            echo NEXT_PUBLIC_API_URL=http://localhost:5001
            echo PORT=5000
        ) > .env.local
        echo Created basic frontend\.env.local file
    )
) else (
    echo frontend\.env.local already exists, skipping
)

echo.
echo === Setup Complete ===
echo.
echo You can now start the services with:
echo   scripts\win-start.bat
echo.
echo Or check status with:
echo   scripts\win-status.bat
echo.
pause

