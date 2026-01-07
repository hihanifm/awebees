@echo off
REM Setup script for LensAI - Run this once before starting services
REM This script sets up the Python virtual environment, installs dependencies,
REM and creates .env files from examples

setlocal enabledelayedexpansion

echo Setting up LensAI...
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
    
    REM Try npm install and capture output to check for SSL errors
    echo Running npm install...
    call npm install >npm_output.tmp 2>&1
    set INSTALL_RESULT=!errorlevel!
    
    REM Check if output contains SSL certificate error
    findstr /C:"UNABLE_TO_GET_ISSUER_CERT_LOCALLY" npm_output.tmp >nul 2>&1
    if not errorlevel 1 (
        set SSL_ERROR=1
    )
    
    REM Clean up temp file
    if exist npm_output.tmp del npm_output.tmp >nul 2>&1
    
    if !INSTALL_RESULT! neq 0 (
        if defined SSL_ERROR (
            echo.
            echo ========================================
            echo SSL Certificate Error Detected
            echo ========================================
            echo.
            echo Error: UNABLE_TO_GET_ISSUER_CERT_LOCALLY
            echo.
            echo This is a common issue on Windows, especially in corporate environments.
            echo.
            echo Would you like to configure npm to handle SSL certificate issues? [Y/N]
            echo WARNING: This will temporarily disable strict SSL verification.
            echo.
            set /p FIX_SSL="Enter choice: "
            
            if /i "!FIX_SSL!"=="Y" (
                echo.
                echo Configuring npm to handle SSL certificate issues...
                call npm config set strict-ssl false
                call npm config set registry https://registry.npmjs.org/
                
                echo.
                echo Retrying npm install with SSL workaround...
                call npm install
                if errorlevel 1 (
                    echo.
                    echo Error: npm install still failing after SSL configuration
                    echo.
                    echo Additional troubleshooting:
                    echo - Check if you're behind a corporate proxy
                    echo - Try: npm config set proxy http://your-proxy:port
                    echo - Try: npm config set https-proxy http://your-proxy:port
                    echo - See WINDOWS-NPM-TROUBLESHOOTING.md for more solutions
                    echo.
                    pause
                    exit /b 1
                )
                echo.
                echo NOTE: SSL strict verification has been disabled for npm.
                echo To re-enable later, run: npm config set strict-ssl true
            ) else (
                echo.
                echo SSL certificate issue not resolved.
                echo.
                echo Manual solutions:
                echo 1. Install proper CA certificates for your system
                echo 2. Configure corporate proxy settings if applicable
                echo 3. See WINDOWS-NPM-TROUBLESHOOTING.md for detailed solutions
                echo.
                pause
                exit /b 1
            )
        ) else (
            echo.
            echo Error: npm install failed with error code !INSTALL_RESULT!
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
                echo - See WINDOWS-NPM-TROUBLESHOOTING.md for SSL certificate solutions
                echo.
                pause
                exit /b 1
            )
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
echo ========================================
echo === Setup Complete ===
echo ========================================
echo.
echo You can now start the services with:
echo   scripts\win-start.bat
echo.
echo Or check status with:
echo   scripts\win-status.bat
echo.
echo ========================================
echo.
echo Would you like to start LensAI now? [Y/N]
set /p LAUNCH_LENS="Enter choice: "

if /i "!LAUNCH_LENS!"=="Y" (
    echo.
    echo ========================================
    echo Launching LensAI...
    echo ========================================
    echo.
    REM Change to script directory and launch
    cd /d "%SCRIPT_DIR%"
    call win-start.bat
    REM Exit after launching (win-start.bat handles its own flow)
    exit /b 0
) else (
    echo.
    echo Setup complete. You can start LensAI later with:
    echo   scripts\win-start.bat
    echo.
    pause
    exit /b 0
)

