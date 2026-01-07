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
REM Check and Install Node.js
REM ===================================
echo === Checking Node.js Installation ===

REM Check if npm is available
where npm >nul 2>&1
if errorlevel 1 (
    echo Node.js/npm is not installed or not in PATH
    echo.
    echo Would you like to install Node.js automatically? [Y/N]
    set /p INSTALL_NODE="Enter choice: "
    
    if /i "!INSTALL_NODE!"=="Y" (
        echo.
        echo Installing Node.js using winget...
        echo This may take a few minutes...
        
        REM Check if winget is available
        where winget >nul 2>&1
        if errorlevel 1 (
            echo Error: winget is not available on this system
            echo.
            echo Please install Node.js manually:
            echo 1. Download from: https://nodejs.org/
            echo 2. Install the LTS version
            echo 3. Restart your command prompt
            echo 4. Run this setup script again
            pause
            exit /b 1
        )
        
        REM Install Node.js LTS using winget
        winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
        
        if errorlevel 1 (
            echo Error: Failed to install Node.js
            echo.
            echo Please install Node.js manually:
            echo 1. Download from: https://nodejs.org/
            echo 2. Install the LTS version
            echo 3. Restart your command prompt
            echo 4. Run this setup script again
            pause
            exit /b 1
        )
        
        echo.
        echo Node.js has been installed successfully!
        echo.
        echo IMPORTANT: You need to restart your command prompt for the changes to take effect.
        echo After restarting, run this setup script again: scripts\win-setup.bat
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo Node.js installation skipped.
        echo.
        echo Please install Node.js manually:
        echo 1. Download from: https://nodejs.org/
        echo 2. Install the LTS version
        echo 3. Restart your command prompt
        echo 4. Run this setup script again
        echo.
        pause
        exit /b 1
    )
) else (
    REM Get Node.js version
    for /f "tokens=*" %%i in ('node --version 2^>nul') do set NODE_VERSION=%%i
    for /f "tokens=*" %%i in ('npm --version 2^>nul') do set NPM_VERSION=%%i
    echo Node.js !NODE_VERSION! detected
    echo npm !NPM_VERSION! detected
    echo.
)

REM ===================================
REM Check and Setup Python
REM ===================================
echo === Checking Python Installation ===

REM Check if python is available
where python >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo.
    echo Would you like to install Python automatically? [Y/N]
    set /p INSTALL_PYTHON="Enter choice: "
    
    if /i "!INSTALL_PYTHON!"=="Y" (
        echo.
        echo Installing Python using winget...
        echo This may take a few minutes...
        
        REM Check if winget is available
        where winget >nul 2>&1
        if errorlevel 1 (
            echo Error: winget is not available on this system
            echo.
            echo Please install Python manually:
            echo 1. Download from: https://www.python.org/downloads/
            echo 2. Install Python 3.9 or later
            echo 3. Make sure to check "Add Python to PATH" during installation
            echo 4. Restart your command prompt
            echo 5. Run this setup script again
            pause
            exit /b 1
        )
        
        REM Install Python using winget
        winget install Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
        
        if errorlevel 1 (
            echo Error: Failed to install Python
            echo.
            echo Please install Python manually:
            echo 1. Download from: https://www.python.org/downloads/
            echo 2. Install Python 3.9 or later
            echo 3. Make sure to check "Add Python to PATH" during installation
            echo 4. Restart your command prompt
            echo 5. Run this setup script again
            pause
            exit /b 1
        )
        
        echo.
        echo Python has been installed successfully!
        echo.
        echo IMPORTANT: You need to restart your command prompt for the changes to take effect.
        echo After restarting, run this setup script again: scripts\win-setup.bat
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo Python installation skipped.
        echo.
        echo Please install Python manually:
        echo 1. Download from: https://www.python.org/downloads/
        echo 2. Install Python 3.9 or later
        echo 3. Make sure to check "Add Python to PATH" during installation
        echo 4. Restart your command prompt
        echo 5. Run this setup script again
        echo.
        pause
        exit /b 1
    )
) else (
    REM Get Python version
    for /f "tokens=*" %%i in ('python --version 2^>nul') do set PYTHON_VERSION=%%i
    echo !PYTHON_VERSION! detected
    echo.
)

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
            echo PORT=34001
            echo HOST=0.0.0.0
            echo FRONTEND_URL=http://localhost:34000
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
    
    REM Clear npm cache to avoid corruption issues
    echo Clearing npm cache...
    call npm cache clean --force >nul 2>&1
    
    REM Try npm install
    call npm install
    if errorlevel 1 (
        echo.
        echo Error: npm install failed with error code !errorlevel!
        echo.
        echo Troubleshooting steps:
        echo 1. Trying to clear npm cache and retry...
        
        REM Remove package-lock.json if it exists (might be corrupted)
        if exist "package-lock.json" (
            echo 2. Removing potentially corrupted package-lock.json...
            del package-lock.json
        )
        
        REM Clear cache again
        call npm cache clean --force
        
        REM Retry installation
        echo 3. Retrying npm install...
        call npm install
        if errorlevel 1 (
            echo.
            echo Error: npm install still failing after troubleshooting attempts
            echo.
            echo Additional troubleshooting:
            echo - Try running as Administrator
            echo - Disable antivirus temporarily
            echo - Check npm logs at: %%APPDATA%%\npm-cache\_logs\
            echo - Try: npm cache verify
            echo - Update npm: npm install -g npm@latest
            echo - Reinstall Node.js from https://nodejs.org/
            echo.
            pause
            exit /b 1
        )
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
            echo NEXT_PUBLIC_API_URL=http://localhost:34001
            echo PORT=34000
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

