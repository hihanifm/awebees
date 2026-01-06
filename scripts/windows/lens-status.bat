@echo off
REM Lens Application Status Script for Windows

echo Checking Lens status...
echo.

REM Check if port 34001 is in use
netstat -ano | findstr :34001 | findstr LISTENING >nul
if errorlevel 1 (
    echo Status: NOT RUNNING
    echo Port 34001 is not in use
) else (
    echo Status: RUNNING
    echo Port 34001 is active
    echo.
    echo Backend URL: http://localhost:34001
)

echo.
pause

