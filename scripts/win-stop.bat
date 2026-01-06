@echo off
REM Stop script for Lens frontend and backend
REM This script stops both services

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PID_FILE=%SCRIPT_DIR%.pids"

if not exist "%PID_FILE%" (
    echo No PID file found. Services are not running ^(or were not started with win-start.bat^).
    exit /b 0
)

echo Stopping Lens services...

set "BACKEND_PID="
set "FRONTEND_PID="

REM Read PIDs from file
for /f "tokens=1,2" %%a in (%PID_FILE%) do (
    if "%%a"=="backend" set "BACKEND_PID=%%b"
    if "%%a"=="frontend" set "FRONTEND_PID=%%b"
)

REM Stop backend
if not "!BACKEND_PID!"=="" (
    tasklist /FI "PID eq !BACKEND_PID!" 2>nul | find "!BACKEND_PID!" >nul
    if not errorlevel 1 (
        echo Stopping backend ^(PID: !BACKEND_PID!^)...
        taskkill /PID !BACKEND_PID! /T /F >nul 2>&1
        echo Backend stopped
    ) else (
        echo Backend was not running
    )
) else (
    echo Backend PID not found in file
)

REM Stop frontend
if not "!FRONTEND_PID!"=="" (
    tasklist /FI "PID eq !FRONTEND_PID!" 2>nul | find "!FRONTEND_PID!" >nul
    if not errorlevel 1 (
        echo Stopping frontend ^(PID: !FRONTEND_PID!^)...
        taskkill /PID !FRONTEND_PID! /T /F >nul 2>&1
        echo Frontend stopped
    ) else (
        echo Frontend was not running
    )
) else (
    echo Frontend PID not found in file
)

REM Cleanup PID file
del "%PID_FILE%" >nul 2>&1

echo.
echo All services stopped.

