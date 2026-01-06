@echo off
REM Lens Application Launcher for Windows
REM Handles both self-contained (with Python) and Python-required variants

setlocal enabledelayedexpansion

echo [DEBUG] Starting Lens launcher...

REM Change to script directory immediately using %~dp0
cd /d "%~dp0"
if errorlevel 1 goto error_no_directory
echo [DEBUG] Changed to directory: %CD%

REM Create logs directory in installation root
echo [DEBUG] Creating logs directory
if not exist "logs" mkdir logs
set "LOG_FILE=%CD%\logs\backend.log"
echo [DEBUG] Log file will be: %LOG_FILE%
REM Test if we can write to the log file
echo [DEBUG] Testing log file write access... > "%LOG_FILE%"
if errorlevel 1 goto logfile_write_warning
echo [DEBUG] Log file write test successful
goto logfile_check_done

:logfile_write_warning
echo [DEBUG] WARNING: Cannot write to log file: %LOG_FILE%
goto logfile_check_done

:logfile_check_done

REM Check if Python directory exists (self-contained variant)
echo [DEBUG] Checking for embedded Python at: python\python.exe
if exist "python\python.exe" goto found_embedded_python
goto check_system_python

:found_embedded_python
echo [DEBUG] Found embedded Python
echo Starting Lens (Self-contained with Python)...
set "PYTHON_EXE=python\python.exe"
set "VARIANT=with-python"
echo [DEBUG] PYTHON_EXE set to: !PYTHON_EXE!
goto check_venv

:check_system_python
echo [DEBUG] Embedded Python not found, checking system Python
echo Starting Lens (Requires Python)...
where python >nul 2>&1
if errorlevel 1 goto error_no_python
echo [DEBUG] System Python found
set "PYTHON_EXE=python"
set "VARIANT=requires-python"
echo [DEBUG] PYTHON_EXE set to: !PYTHON_EXE!
goto check_venv

:check_venv
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Checking for venv
if exist "venv\Scripts\activate.bat" goto activate_existing_venv
goto create_new_venv

:activate_existing_venv
echo [DEBUG] Virtual environment exists, activating...
call venv\Scripts\activate.bat
if errorlevel 1 goto error_activate_venv
echo [DEBUG] Virtual environment activated
goto start_backend

:create_new_venv
echo [DEBUG] Creating virtual environment...
echo Creating virtual environment...
"!PYTHON_EXE!" -m venv venv
if errorlevel 1 goto error_create_venv
echo [DEBUG] Virtual environment created, activating...
call venv\Scripts\activate.bat
if errorlevel 1 goto error_activate_new_venv
echo [DEBUG] Virtual environment activated
echo [DEBUG] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto error_upgrade_pip
python -m pip install -r backend\requirements.txt
if errorlevel 1 goto error_install_deps
echo [DEBUG] Dependencies installed
goto start_backend

:start_backend
echo [DEBUG] Setting SERVE_FRONTEND=true
set SERVE_FRONTEND=true
REM Store installation root before changing directories
set "INSTALL_ROOT=%CD%"
echo [DEBUG] Installation root: %INSTALL_ROOT%
echo [DEBUG] Changing to backend directory
cd /d backend
if errorlevel 1 goto error_backend_dir
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Starting backend server
echo Starting Lens backend on http://127.0.0.1:34001...
echo [DEBUG] Logs will be written to: %LOG_FILE%
REM Ensure log file exists and is writable
if not exist "%LOG_FILE%" echo. > "%LOG_FILE%"
if errorlevel 1 goto error_create_logfile
REM Use Python unbuffered mode (-u) and ensure proper redirection
REM The -u flag makes Python output unbuffered, so logs appear immediately
REM Create a temporary file to write the startup marker, avoiding path issues
set "TEMP_MARKER=%TEMP%\lens-marker-%RANDOM%.txt"
echo ======================================== > "%TEMP_MARKER%"
echo Lens Backend Started: %DATE% %TIME% >> "%TEMP_MARKER%"
echo ======================================== >> "%TEMP_MARKER%"
type "%TEMP_MARKER%" >> "%LOG_FILE%"
del "%TEMP_MARKER%" >nul 2>&1
start "Lens Backend" /min cmd /c "cd /d %CD% && python -u -m uvicorn app.main:app --host 0.0.0.0 --port 34001 >> \"%LOG_FILE%\" 2>&1"
if errorlevel 1 goto error_start_backend
echo [DEBUG] Backend started
echo [DEBUG] Log file location: %LOG_FILE%
echo [DEBUG] You can view logs with: lens-logs.bat
goto backend_started

:error_create_logfile
echo [DEBUG] ERROR: Cannot create log file: %LOG_FILE%
goto error_start_backend

:backend_started
echo [DEBUG] Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul
echo [DEBUG] Wait complete
echo [DEBUG] Opening browser to http://127.0.0.1:34001
start http://127.0.0.1:34001
echo.
echo Lens is starting...
echo Backend: http://127.0.0.1:34001
echo.
echo Press any key to close this window (Lens will continue running in background)
pause >nul
exit /b 0

:error_no_directory
echo [DEBUG] ERROR: Failed to change to script directory
echo ERROR: Cannot access installation directory
pause
exit /b 1

:error_no_python
echo [DEBUG] System Python not found in PATH
echo ERROR: Python is not installed or not in PATH
echo Please install Python 3.x from https://www.python.org/
pause
exit /b 1

:error_activate_venv
echo [DEBUG] ERROR: Failed to activate virtual environment
echo ERROR: Failed to activate virtual environment
pause
exit /b 1

:error_create_venv
echo [DEBUG] ERROR: Failed to create virtual environment
echo ERROR: Failed to create virtual environment
pause
exit /b 1

:error_activate_new_venv
echo [DEBUG] ERROR: Failed to activate newly created virtual environment
echo ERROR: Failed to activate newly created virtual environment
pause
exit /b 1

:error_upgrade_pip
echo [DEBUG] ERROR: Failed to upgrade pip
echo ERROR: Failed to upgrade pip
pause
exit /b 1

:error_install_deps
echo [DEBUG] ERROR: Failed to install dependencies
echo ERROR: Failed to install dependencies
pause
exit /b 1

:error_backend_dir
echo [DEBUG] ERROR: Failed to change to backend directory
echo ERROR: Failed to change to backend directory
pause
exit /b 1

:error_start_backend
echo [DEBUG] ERROR: Failed to start backend
echo ERROR: Failed to start backend
pause
exit /b 1
