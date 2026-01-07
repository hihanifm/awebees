@echo off
REM Status script for Lens frontend and backend
REM This script checks if the services are running

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PID_FILE=%SCRIPT_DIR%.pids"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if not exist "%PID_FILE%" (
    echo No PID file found. Services are not running ^(or were not started with win-start.bat^).
    exit /b 0
)

set "BACKEND_PID="
set "FRONTEND_PID="

REM Read PIDs from file
for /f "tokens=1,2" %%a in (%PID_FILE%) do (
    if "%%a"=="backend" set "BACKEND_PID=%%b"
    if "%%a"=="frontend" set "FRONTEND_PID=%%b"
)

REM Load ports from env files (match win-start behavior)
set "BACKEND_PORT=34001"
set "FRONTEND_PORT=34000"

if exist "%PROJECT_ROOT%\backend\.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\backend\.env") do (
        if "%%a"=="PORT" (
            set "BACKEND_PORT=%%b"
            set "BACKEND_PORT=!BACKEND_PORT:"=!"
            set "BACKEND_PORT=!BACKEND_PORT: =!"
            for /f "tokens=*" %%x in ("!BACKEND_PORT!") do set "BACKEND_PORT=%%x"
        )
    )
)

if exist "%PROJECT_ROOT%\frontend\.env.local" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%PROJECT_ROOT%\frontend\.env.local") do (
        if "%%a"=="PORT" (
            set "FRONTEND_PORT=%%b"
            set "FRONTEND_PORT=!FRONTEND_PORT:"=!"
            set "FRONTEND_PORT=!FRONTEND_PORT: =!"
            for /f "tokens=*" %%x in ("!FRONTEND_PORT!") do set "FRONTEND_PORT=%%x"
        )
    )
)

echo Lens Services Status
echo ======================
echo.

REM Check backend
if not "!BACKEND_PID!"=="" (
    tasklist /FI "PID eq !BACKEND_PID!" 2>nul | find "!BACKEND_PID!" >nul
    if not errorlevel 1 (
        echo Backend: RUNNING ^(PID: !BACKEND_PID!, Port: !BACKEND_PORT!^)
    ) else (
        echo Backend: NOT RUNNING
    )
) else (
    echo Backend: NOT RUNNING
)

REM Check frontend
if not "!FRONTEND_PID!"=="" (
    tasklist /FI "PID eq !FRONTEND_PID!" 2>nul | find "!FRONTEND_PID!" >nul
    if not errorlevel 1 (
        echo Frontend: RUNNING ^(PID: !FRONTEND_PID!, Port: !FRONTEND_PORT!^)
    ) else (
        echo Frontend: NOT RUNNING
    )
) else (
    echo Frontend: NOT RUNNING ^(Production mode - served by backend^)
)

echo.

