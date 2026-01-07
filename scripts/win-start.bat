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
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\backend\.env") do (
        if "%%a"=="PORT" (
            set "BACKEND_PORT=%%b"
            REM Remove quotes, spaces, and carriage returns
            set "BACKEND_PORT=!BACKEND_PORT:"=!"
            set "BACKEND_PORT=!BACKEND_PORT: =!"
            for /f "tokens=*" %%x in ("!BACKEND_PORT!") do set "BACKEND_PORT=%%x"
        )
        if "%%a"=="HOST" (
            set "BACKEND_HOST=%%b"
            REM Remove quotes, spaces, and carriage returns
            set "BACKEND_HOST=!BACKEND_HOST:"=!"
            set "BACKEND_HOST=!BACKEND_HOST: =!"
            for /f "tokens=*" %%x in ("!BACKEND_HOST!") do set "BACKEND_HOST=%%x"
        )
    )
)

REM ===================================
REM Load Frontend Environment Variables
REM ===================================
set "FRONTEND_PORT=34000"

if exist "%PROJECT_ROOT%\frontend\.env.local" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\frontend\.env.local") do (
        if "%%a"=="PORT" (
            set "FRONTEND_PORT=%%b"
            REM Remove quotes, spaces, and carriage returns
            set "FRONTEND_PORT=!FRONTEND_PORT:"=!"
            set "FRONTEND_PORT=!FRONTEND_PORT: =!"
            for /f "tokens=*" %%x in ("!FRONTEND_PORT!") do set "FRONTEND_PORT=%%x"
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
if "%MODE%"=="prod" goto start_frontend

REM NOTE: Use CMD escaping (^") not backslash escaping (\") inside cmd /c strings.
start "" /b cmd /v:on /c "call venv\Scripts\activate.bat ^&^& uvicorn app.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT% ^>^> ^\"%BACKEND_LOG%^\" 2^>^&1"

REM Wait for backend to start (uvicorn with reload can take longer on Windows)
call :wait_for_listening_pid %BACKEND_PORT% BACKEND_PID 20
if not "%BACKEND_PID%"=="" goto backend_ok

echo Error: Backend failed to start - no process listening on port %BACKEND_PORT%
echo Check backend logs: %BACKEND_LOG%
type "%BACKEND_LOG%" 2>nul | more
pause
exit /b 1

:backend_ok
echo Backend started ^(PID: %BACKEND_PID%, Port: %BACKEND_PORT%^)

REM ===================================
REM Start Frontend
REM ===================================
:start_frontend
cd /d "%PROJECT_ROOT%\frontend"

if not exist "node_modules" (
    echo Error: Node.js dependencies not found in frontend\node_modules
    echo Please run scripts\win-setup.bat first to install dependencies
    if not "%MODE%"=="prod" taskkill /PID !BACKEND_PID! /F >nul 2>&1
    pause
    exit /b 1
)

if "%MODE%"=="prod" goto prod_mode

REM Development mode: Start separate frontend server
echo Starting frontend in DEVELOPMENT mode on port %FRONTEND_PORT%...
start "" /b cmd /v:on /c "set PORT=%FRONTEND_PORT% ^&^& call npm run dev ^>^> ^\"%FRONTEND_LOG%^\" 2^>^&1"

REM Wait for frontend to start (Next.js takes longer)
call :wait_for_listening_pid %FRONTEND_PORT% FRONTEND_PID 30
if "%FRONTEND_PID%"=="" (
    echo Error: Frontend failed to start - no process listening on port %FRONTEND_PORT%
    echo Check frontend logs: %FRONTEND_LOG%
    type "%FRONTEND_LOG%" | more
    if not "%MODE%"=="prod" taskkill /PID %BACKEND_PID% /F >nul 2>&1
    pause
    exit /b 1
)

REM Save PIDs
echo backend %BACKEND_PID% > "%PID_FILE%"
echo frontend %FRONTEND_PID% >> "%PID_FILE%"

echo.
echo Services started successfully in DEVELOPMENT mode!
echo Backend: http://localhost:%BACKEND_PORT% ^(PID: %BACKEND_PID%^)
echo Frontend: http://localhost:%FRONTEND_PORT% ^(PID: %FRONTEND_PID%^)
echo.
echo Logs:
echo   Backend: %BACKEND_LOG%
echo   Frontend: %FRONTEND_LOG%
echo.
echo Use 'scripts\win-status.bat' to check status
echo Use 'scripts\win-stop.bat' to stop services
echo.
exit /b 0

:prod_mode
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
start "" /b cmd /v:on /c "call venv\Scripts\activate.bat ^&^& set SERVE_FRONTEND=true ^&^& uvicorn app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT% ^>^> ^\"%BACKEND_LOG%^\" 2^>^&1"

REM Wait for backend to start
call :wait_for_listening_pid %BACKEND_PORT% BACKEND_PID 20
if "%BACKEND_PID%"=="" (
    echo Error: Backend failed to start in production mode - no process listening on port %BACKEND_PORT%
    echo Check backend logs: %BACKEND_LOG%
    type "%BACKEND_LOG%" 2>nul | more
    pause
    exit /b 1
)

REM Save PID (only backend in production)
echo backend %BACKEND_PID% > "%PID_FILE%"

echo.
echo Services started successfully in PRODUCTION mode!
echo Backend ^(serving API + Frontend^): http://localhost:%BACKEND_PORT% ^(PID: %BACKEND_PID%^)
echo.
echo Logs:
echo   Backend: %BACKEND_LOG%
echo.
echo Use 'scripts\win-status.bat' to check status
echo Use 'scripts\win-stop.bat' to stop services
echo.
exit /b 0

:find_listening_pid
setlocal
set "PORT=%~1"
set "PID="
REM Use a tolerant netstat filter (works for IPv4/IPv6 and variable spacing)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%PORT%" 2^>nul') do (
    set "PID=%%a"
    goto :pid_done
)
:pid_done
endlocal & set "%~2=%PID%"
exit /b 0

:wait_for_listening_pid
REM Args: <port> <outVarName> <maxSeconds>
setlocal enabledelayedexpansion
set "PORT=%~1"
set "OUTVAR=%~2"
set "MAX=%~3"
if "%MAX%"=="" set "MAX=15"
set "PID="
set /a "I=0"
:wait_loop
call :find_listening_pid %PORT% PID
if not "!PID!"=="" goto wait_done
set /a "I+=1"
if !I! GEQ %MAX% goto wait_done
timeout /t 1 /nobreak >nul
goto wait_loop
:wait_done
endlocal & set "%~2=%PID%"
exit /b 0
