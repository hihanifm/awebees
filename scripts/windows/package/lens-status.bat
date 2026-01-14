@echo off
REM Lens Application Status Script for Windows

echo Checking Lens status...
echo.

REM Load backend PORT from backend\.env if present (default: 34001)
setlocal enabledelayedexpansion
set "BACKEND_PORT=34001"
cd /d "%~dp0"
if exist "backend\.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("backend\.env") do (
        if "%%a"=="PORT" (
            set "BACKEND_PORT=%%b"
            set "BACKEND_PORT=!BACKEND_PORT:"=!"
            set "BACKEND_PORT=!BACKEND_PORT: =!"
            for /f "tokens=*" %%x in ("!BACKEND_PORT!") do set "BACKEND_PORT=%%x"
        )
    )
)

REM Check if backend port is in use
netstat -ano | findstr ":!BACKEND_PORT!" | findstr LISTENING >nul
if errorlevel 1 (
    echo Status: NOT RUNNING
    echo Port !BACKEND_PORT! is not in use
) else (
    echo Status: RUNNING
    echo Port !BACKEND_PORT! is active
    echo.
    echo Backend URL: http://127.0.0.1:!BACKEND_PORT!
)

echo.
pause

