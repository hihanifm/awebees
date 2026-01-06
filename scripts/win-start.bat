@echo off
REM Start script for Lens frontend and backend
REM This script starts both services as background processes
REM Usage: win-start.bat [-p] [-h]
REM   -p: Production mode (uses next start instead of next dev)
REM   -h: Show help

setlocal enabledelayedexpansion

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "PID_FILE=%SCRIPT_DIR%.pids"
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "BACKEND_LOG=%LOGS_DIR%\backend.log"
set "FRONTEND_LOG=%LOGS_DIR%\frontend.log"

REM Create logs directory if it doesn't exist
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Parse arguments
set "MODE=dev"
set "SHOW_HELP=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="-p" set "MODE=prod" & shift & goto parse_args
if /i "%~1"=="--prod" set "MODE=prod" & shift & goto parse_args
if /i "%~1"=="--production" set "MODE=prod" & shift & goto parse_args
if /i "%~1"=="-h" set "SHOW_HELP=1" & shift & goto parse_args
if /i "%~1"=="--help" set "SHOW_HELP=1" & shift & goto parse_args
echo Unknown option: %~1
echo Use -h or --help for usage information
exit /b 1

:args_done

if "%SHOW_HELP%"=="1" (
    echo Usage: win-start.bat [-p^|--prod] [-h^|--help]
    echo.
    echo Options:
    echo   -p, --prod, --production  Start in production mode ^(default: development^)
    echo   -h, --help                Show this help message
    echo.
    echo Modes:
    echo   Development ^(default^): Uses 'next dev' for frontend with hot reload
    echo   Production ^(-p^):       Uses 'next start' for frontend ^(requires build first^)
    exit /b 0
)

REM Set NODE_ENV for Next.js
if "%MODE%"=="prod" (
    set "NODE_ENV=production"
) else (
    set "NODE_ENV=development"
)

REM Check if processes are already running
if exist "%PID_FILE%" (
    for /f "tokens=1,2" %%a in (%PID_FILE%) do (
        if "%%a"=="backend" (
            tasklist /FI "PID eq %%b" 2>nul | find "%%b" >nul
            if not errorlevel 1 (
                echo Backend is already running ^(PID: %%b^)
                exit /b 1
            )
        )
        if "%%a"=="frontend" (
            tasklist /FI "PID eq %%b" 2>nul | find "%%b" >nul
            if not errorlevel 1 (
                echo Frontend is already running ^(PID: %%b^)
                exit /b 1
            )
        )
    )
)

if "%MODE%"=="prod" (
    echo Starting Lens services in PRODUCTION mode...
) else (
    echo Starting Lens services in DEVELOPMENT mode...
)

REM ===================================
REM Load Backend Environment Variables
REM ===================================
set "BACKEND_PORT=34001"
set "BACKEND_HOST=0.0.0.0"

if exist "%PROJECT_ROOT%\backend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\backend\.env") do (
        set "LINE=%%a"
        if not "!LINE:~0,1!"=="#" (
            if "%%a"=="PORT" set "BACKEND_PORT=%%b"
            if "%%a"=="HOST" set "BACKEND_HOST=%%b"
        )
    )
)

REM ===================================
REM Load Frontend Environment Variables
REM ===================================
set "FRONTEND_PORT=34000"

if exist "%PROJECT_ROOT%\frontend\.env.local" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\frontend\.env.local") do (
        set "LINE=%%a"
        if not "!LINE:~0,1!"=="#" (
            if "%%a"=="PORT" set "FRONTEND_PORT=%%b"
        )
    )
)

REM ===================================
REM Start Backend
REM ===================================
echo Starting backend on port %BACKEND_PORT%...
cd /d "%PROJECT_ROOT%\backend"

if not exist "venv" (
    echo Error: Python virtual environment not found in backend\venv
    echo Please run scripts\win-setup.bat first to set up the project
    pause
    exit /b 1
)

REM Start backend (will be restarted in prod mode after frontend build)
if not "%MODE%"=="prod" (
    start /b cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT% > "%BACKEND_LOG%" 2>&1"
    
    REM Wait for backend to start
    timeout /t 3 /nobreak >nul
    
    REM Get PID of the backend process (find python.exe listening on backend port)
    set "BACKEND_PID="
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr "LISTENING"') do set "BACKEND_PID=%%a"
    
    REM Verify backend is running by checking if PID exists and port is listening
    if "!BACKEND_PID!"=="" (
        echo Error: Backend failed to start - no process listening on port %BACKEND_PORT%
        echo Check backend logs: %BACKEND_LOG%
        type "%BACKEND_LOG%" | more
        pause
        exit /b 1
    )
    
    tasklist /FI "PID eq !BACKEND_PID!" 2>nul | find "!BACKEND_PID!" >nul
    if errorlevel 1 (
        echo Error: Backend process not found
        echo Check backend logs: %BACKEND_LOG%
        type "%BACKEND_LOG%" | more
        pause
        exit /b 1
    )
    
    echo Backend started ^(PID: !BACKEND_PID!, Port: %BACKEND_PORT%^)
)

REM ===================================
REM Start Frontend
REM ===================================
cd /d "%PROJECT_ROOT%\frontend"

if not exist "node_modules" (
    echo Error: Node.js dependencies not found in frontend\node_modules
    echo Please run scripts\win-setup.bat first to install dependencies
    if not "%MODE%"=="prod" taskkill /PID !BACKEND_PID! /F >nul 2>&1
    pause
    exit /b 1
)

if "%MODE%"=="prod" (
    REM Production mode: Build frontend and serve from backend
    echo Building frontend for production...
    
    call npm run build
    if errorlevel 1 (
        echo Error: Frontend build failed
        pause
        exit /b 1
    )
    
    if not exist "out" (
        echo Error: Frontend build output not found. Expected 'out' directory.
        pause
        exit /b 1
    )
    
    echo Frontend built successfully
    
    REM Start backend with SERVE_FRONTEND enabled
    cd /d "%PROJECT_ROOT%\backend"
    set "SERVE_FRONTEND=true"
    start /b cmd /c "call venv\Scripts\activate.bat && set SERVE_FRONTEND=true && uvicorn app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT% > "%BACKEND_LOG%" 2>&1"
    
    REM Wait for backend to start
    timeout /t 3 /nobreak >nul
    
    REM Get PID of the backend process (find python.exe listening on backend port)
    set "BACKEND_PID="
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr "LISTENING"') do set "BACKEND_PID=%%a"
    
    REM Verify backend is running by checking if PID exists and port is listening
    if "!BACKEND_PID!"=="" (
        echo Error: Backend failed to restart with frontend serving - no process listening on port %BACKEND_PORT%
        echo Check backend logs: %BACKEND_LOG%
        type "%BACKEND_LOG%" | more
        pause
        exit /b 1
    )
    
    tasklist /FI "PID eq !BACKEND_PID!" 2>nul | find "!BACKEND_PID!" >nul
    if errorlevel 1 (
        echo Error: Backend process not found
        echo Check backend logs: %BACKEND_LOG%
        type "%BACKEND_LOG%" | more
        pause
        exit /b 1
    )
    
    REM Save PID (only backend in production)
    echo backend !BACKEND_PID! > "%PID_FILE%"
    
    echo.
    echo Services started successfully in PRODUCTION mode!
    echo Backend ^(serving API + Frontend^): http://localhost:%BACKEND_PORT% ^(PID: !BACKEND_PID!^)
    echo.
    echo Logs:
    echo   Backend: %BACKEND_LOG%
    echo.
    echo Use 'scripts\win-status.bat' to check status
    echo Use 'scripts\win-stop.bat' to stop services
    
) else (
    REM Development mode: Start separate frontend server
    echo Starting frontend in DEVELOPMENT mode on port %FRONTEND_PORT%...
    
    cd /d "%PROJECT_ROOT%\frontend"
    start /b cmd /c "set PORT=%FRONTEND_PORT% && call npm run dev > "%FRONTEND_LOG%" 2>&1"
    
    REM Wait for frontend to start (Next.js takes longer)
    timeout /t 5 /nobreak >nul
    
    REM Get PID of the frontend process (find node.exe listening on frontend port)
    set "FRONTEND_PID="
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr "LISTENING"') do set "FRONTEND_PID=%%a"
    
    REM Verify frontend is running by checking if PID exists and port is listening
    if "!FRONTEND_PID!"=="" (
        echo Error: Frontend failed to start - no process listening on port %FRONTEND_PORT%
        echo Check frontend logs: %FRONTEND_LOG%
        type "%FRONTEND_LOG%" | more
        REM Clean up backend if frontend failed
        taskkill /PID !BACKEND_PID! /F >nul 2>&1
        pause
        exit /b 1
    )
    
    tasklist /FI "PID eq !FRONTEND_PID!" 2>nul | find "!FRONTEND_PID!" >nul
    if errorlevel 1 (
        echo Error: Frontend process not found
        echo Check frontend logs: %FRONTEND_LOG%
        type "%FRONTEND_LOG%" | more
        REM Clean up backend if frontend failed
        taskkill /PID !BACKEND_PID! /F >nul 2>&1
        pause
        exit /b 1
    )
    
    REM Save PIDs
    echo backend !BACKEND_PID! > "%PID_FILE%"
    echo frontend !FRONTEND_PID! >> "%PID_FILE%"
    
    echo.
    echo Services started successfully in DEVELOPMENT mode!
    echo Backend: http://localhost:%BACKEND_PORT% ^(PID: !BACKEND_PID!^)
    echo Frontend: http://localhost:%FRONTEND_PORT% ^(PID: !FRONTEND_PID!^)
    echo.
    echo Logs:
    echo   Backend: %BACKEND_LOG%
    echo   Frontend: %FRONTEND_LOG%
    echo.
    echo Use 'scripts\win-status.bat' to check status
    echo Use 'scripts\win-stop.bat' to stop services
)

echo.

