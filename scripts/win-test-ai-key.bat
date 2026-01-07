@echo off
REM Test OpenAI API key and connection for Lens
REM Usage: scripts\win-test-ai-key.bat

setlocal

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Use the virtual environment's Python
set PYTHON=%PROJECT_ROOT%\backend\venv\Scripts\python.exe

REM Check if virtual environment exists
if not exist "%PYTHON%" (
    echo ❌ Error: Virtual environment not found
    echo.
    echo Please run setup first:
    echo   scripts\win-setup.bat
    exit /b 1
)

REM Run the test script
"%PYTHON%" "%SCRIPT_DIR%test-ai-key.py" %*

