@echo off
REM Lens Application Stop Script for Windows

echo Stopping Lens backend...

REM Find and kill uvicorn processes
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr /i "PID"') do (
    taskkill /pid %%a /f >nul 2>&1
)

REM Also try to kill by window title
taskkill /fi "WindowTitle eq Lens Backend*" /f >nul 2>&1

REM Kill any process using port 34001 (requires netstat and findstr)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :34001 ^| findstr LISTENING') do (
    taskkill /pid %%a /f >nul 2>&1
)

echo Lens backend stopped.

