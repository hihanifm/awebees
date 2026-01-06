@echo off
REM Status script for Lens frontend and backend
REM This script checks if the services are running

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PID_FILE=%SCRIPT_DIR%.pids"

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

echo Lens Services Status
echo ======================
echo.

REM Check backend
if not "!BACKEND_PID!"=="" (
    tasklist /FI "PID eq !BACKEND_PID!" 2>nul | find "!BACKEND_PID!" >nul
    if not errorlevel 1 (
        echo [92m✓[0m Backend: RUNNING ^(PID: !BACKEND_PID!, Port: 34001^)
    ) else (
        echo [91m✗[0m Backend: NOT RUNNING
    )
) else (
    echo [91m✗[0m Backend: NOT RUNNING
)

REM Check frontend
if not "!FRONTEND_PID!"=="" (
    tasklist /FI "PID eq !FRONTEND_PID!" 2>nul | find "!FRONTEND_PID!" >nul
    if not errorlevel 1 (
        echo [92m✓[0m Frontend: RUNNING ^(PID: !FRONTEND_PID!, Port: 34000^)
    ) else (
        echo [91m✗[0m Frontend: NOT RUNNING
    )
) else (
    echo [91m✗[0m Frontend: NOT RUNNING ^(Production mode - served by backend^)
)

echo.

