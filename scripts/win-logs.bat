@echo off
REM View logs script for Lens
REM Shows the last 20 lines of frontend or backend logs

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "BACKEND_LOG=%LOGS_DIR%\backend.log"
set "FRONTEND_LOG=%LOGS_DIR%\frontend.log"

REM Default to frontend if no argument provided
set "SHOW_FRONTEND=1"
set "SHOW_BACKEND=0"

REM Parse arguments
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="-f" set "SHOW_FRONTEND=1" & set "SHOW_BACKEND=0" & shift & goto parse_args
if /i "%~1"=="--frontend" set "SHOW_FRONTEND=1" & set "SHOW_BACKEND=0" & shift & goto parse_args
if /i "%~1"=="-b" set "SHOW_FRONTEND=0" & set "SHOW_BACKEND=1" & shift & goto parse_args
if /i "%~1"=="--backend" set "SHOW_FRONTEND=0" & set "SHOW_BACKEND=1" & shift & goto parse_args
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
echo Unknown option: %~1
echo Use -h or --help for usage information
exit /b 1

:args_done

REM Show logs
if "%SHOW_FRONTEND%"=="1" (
    if exist "%FRONTEND_LOG%" (
        echo === Frontend Logs ^(last 20 lines^) ===
        echo File: %FRONTEND_LOG%
        echo.
        REM Use PowerShell to get last 20 lines (more reliable than batch)
        powershell -Command "Get-Content '%FRONTEND_LOG%' -Tail 20"
    ) else (
        echo Frontend log file not found: %FRONTEND_LOG%
        exit /b 1
    )
) else if "%SHOW_BACKEND%"=="1" (
    if exist "%BACKEND_LOG%" (
        echo === Backend Logs ^(last 20 lines^) ===
        echo File: %BACKEND_LOG%
        echo.
        REM Use PowerShell to get last 20 lines (more reliable than batch)
        powershell -Command "Get-Content '%BACKEND_LOG%' -Tail 20"
    ) else (
        echo Backend log file not found: %BACKEND_LOG%
        exit /b 1
    )
)

echo.
goto :eof

:show_help
echo Usage: win-logs.bat [-f^|--frontend] [-b^|--backend]
echo.
echo Options:
echo   -f, --frontend  Show frontend logs ^(default^)
echo   -b, --backend   Show backend logs
echo   -h, --help      Show this help message
echo.
exit /b 0

