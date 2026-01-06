@echo off
REM Lens Application Log Viewer for Windows
REM Shows the last 20 lines of backend logs

setlocal enabledelayedexpansion

REM Change to script directory
cd /d "%~dp0"
if errorlevel 1 goto error_no_directory

set "LOG_FILE=%CD%\logs\backend.log"

REM Check if log file exists
if not exist "!LOG_FILE!" (
    echo Log file not found: !LOG_FILE!
    echo.
    echo Make sure Lens backend has been started at least once.
    pause
    exit /b 1
)

echo === Backend Logs (last 20 lines) ===
echo File: !LOG_FILE!
echo.
powershell -Command "Get-Content '!LOG_FILE!' -Tail 20"
echo.
echo.
echo To view logs in real-time, use:
echo   powershell -Command "Get-Content '!LOG_FILE!' -Wait -Tail 20"
echo.
pause
exit /b 0

:error_no_directory
echo ERROR: Cannot access installation directory
pause
exit /b 1

