@echo off
REM Lens Application Launcher for Windows
REM Handles both self-contained (with Python) and Python-required variants

setlocal enabledelayedexpansion

echo [DEBUG] Starting Lens launcher...

REM Change to script directory immediately using %~dp0
cd /d "%~dp0"
if errorlevel 1 goto error_no_directory
echo [DEBUG] Changed to directory: %CD%

REM Add bin directory to PATH for optional tools (like ripgrep)
if exist "bin" (
    set "PATH=%CD%\bin;%PATH%"
    echo [DEBUG] Added bin directory to PATH
)

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
goto start_tray

:start_tray
REM Store installation root
set "INSTALL_ROOT=%CD%"

REM Get the full path to pythonw.exe in the venv (no console window)
set "VENV_PYTHONW=%INSTALL_ROOT%\venv\Scripts\pythonw.exe"
REM Tray script should be in the same directory as this script (installation root)
set "TRAY_SCRIPT=%~dp0lens_tray.py"

REM Check if pythonw.exe exists
if not exist "!VENV_PYTHONW!" (
    echo ERROR: pythonw.exe not found in venv
    echo Expected: !VENV_PYTHONW!
    echo Please ensure the virtual environment is set up correctly.
    pause
    exit /b 1
)

REM Check if tray script exists
if not exist "!TRAY_SCRIPT!" (
    echo ERROR: Tray application script not found
    echo Expected: !TRAY_SCRIPT!
    pause
    exit /b 1
)

REM Launch tray application using pythonw.exe (no console window)
REM This will show the system tray icon and exit this script immediately
start "" "!VENV_PYTHONW!" "!TRAY_SCRIPT!"
if errorlevel 1 goto error_start_tray

REM Exit immediately - tray app is now running
exit /b 0

:error_start_tray
echo ERROR: Failed to start tray application
pause
exit /b 1

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

