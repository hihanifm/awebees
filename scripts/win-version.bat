@echo off
REM Version management script for Lens
REM Usage: win-version.bat [command] [version]
REM Commands:
REM   get        - Show current version (default)
REM   set        - Set version (requires version argument, e.g., 0.1.0)
REM   bump       - Bump version (major|minor|patch)
REM   sync       - Sync version to package.json
REM   sync-docs  - Detect version from installer files and update docs/index.html

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "VERSION_FILE=%PROJECT_ROOT%\VERSION"
set "PACKAGE_JSON=%PROJECT_ROOT%\frontend\package.json"

REM Get command (default to 'get')
set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=get"

REM Execute command
if /i "%COMMAND%"=="get" goto cmd_get
if /i "%COMMAND%"=="set" goto cmd_set
if /i "%COMMAND%"=="bump" goto cmd_bump
if /i "%COMMAND%"=="sync" goto cmd_sync
if /i "%COMMAND%"=="sync-docs" goto cmd_sync_docs
goto cmd_help

:cmd_get
call :get_current_version VERSION
echo %VERSION%
goto :eof

:cmd_set
set "NEW_VERSION=%~2"
if "%NEW_VERSION%"=="" (
    echo Error: Version argument required
    echo Usage: win-version.bat set ^<version^>
    exit /b 1
)

REM Validate version format (basic semantic version check)
echo %NEW_VERSION% | findstr /R "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo %NEW_VERSION% | findstr /R "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*-[a-zA-Z0-9.-][a-zA-Z0-9.-]*$" >nul
    if errorlevel 1 (
        echo Error: Invalid version format. Expected: X.Y.Z or X.Y.Z-label
        exit /b 1
    )
)

echo %NEW_VERSION% > "%VERSION_FILE%"
echo Version set to: %NEW_VERSION%

REM Sync to package.json
call :sync_to_package_json "%NEW_VERSION%"
goto :eof

:cmd_bump
set "BUMP_TYPE=%~2"
if "%BUMP_TYPE%"=="" (
    echo Error: Bump type required
    echo Usage: win-version.bat bump ^<major^|minor^|patch^>
    exit /b 1
)

call :get_current_version CURRENT_VERSION

REM Remove any pre-release suffix for bumping
for /f "tokens=1 delims=-" %%a in ("%CURRENT_VERSION%") do set "BASE_VERSION=%%a"

REM Parse version parts
for /f "tokens=1,2,3 delims=." %%a in ("%BASE_VERSION%") do (
    set "MAJOR=%%a"
    set "MINOR=%%b"
    set "PATCH=%%c"
)

REM Bump version
if /i "%BUMP_TYPE%"=="major" (
    set /a MAJOR+=1
    set "MINOR=0"
    set "PATCH=0"
) else if /i "%BUMP_TYPE%"=="minor" (
    set /a MINOR+=1
    set "PATCH=0"
) else if /i "%BUMP_TYPE%"=="patch" (
    set /a PATCH+=1
) else (
    echo Error: Invalid bump type. Use: major^|minor^|patch
    exit /b 1
)

set "NEW_VERSION=!MAJOR!.!MINOR!.!PATCH!"
echo %NEW_VERSION% > "%VERSION_FILE%"
echo Version set to: %NEW_VERSION%

REM Sync to package.json
call :sync_to_package_json "%NEW_VERSION%"
goto :eof

:cmd_sync
call :get_current_version VERSION
call :sync_to_package_json "%VERSION%"
echo Version synced to package.json
goto :eof

:cmd_sync_docs
set "DIST_DIR=%PROJECT_ROOT%\dist\windows"
set "DOCS_HTML=%PROJECT_ROOT%\docs\index.html"

if not exist "%DIST_DIR%" (
    echo Error: dist\windows directory not found
    exit /b 1
)

if not exist "%DOCS_HTML%" (
    echo Error: docs\index.html not found
    exit /b 1
)

REM Find installer files
set "WITH_PYTHON_FILE="
set "REQUIRES_PYTHON_FILE="

for %%f in ("%DIST_DIR%\lens-package-with-python-*.zip") do set "WITH_PYTHON_FILE=%%f"
for %%f in ("%DIST_DIR%\lens-package-requires-python-*.zip") do set "REQUIRES_PYTHON_FILE=%%f"

if "%WITH_PYTHON_FILE%"=="" (
    echo Error: lens-package-with-python-*.zip not found in dist\windows\
    exit /b 1
)

if "%REQUIRES_PYTHON_FILE%"=="" (
    echo Error: lens-package-requires-python-*.zip not found in dist\windows\
    exit /b 1
)

REM Extract version from filename
for %%f in ("%WITH_PYTHON_FILE%") do set "FILENAME=%%~nf"
set "VERSION1=%FILENAME:lens-package-with-python-=%"

for %%f in ("%REQUIRES_PYTHON_FILE%") do set "FILENAME=%%~nf"
set "VERSION2=%FILENAME:lens-package-requires-python-=%"

if not "%VERSION1%"=="%VERSION2%" (
    echo Error: Version mismatch in installer files
    echo   with-python version: %VERSION1%
    echo   requires-python version: %VERSION2%
    exit /b 1
)

set "DETECTED_VERSION=%VERSION1%"

REM Replace {VERSION} placeholder in HTML file using PowerShell
powershell -Command "(Get-Content '%DOCS_HTML%') -replace '\{VERSION\}', '%DETECTED_VERSION%' | Set-Content '%DOCS_HTML%'"

echo Synced version %DETECTED_VERSION% to docs\index.html
goto :eof

:cmd_help
echo Usage: win-version.bat [get^|set^|bump^|sync^|sync-docs] [version^|bump_type]
echo.
echo Commands:
echo   get              Show current version ^(default^)
echo   set ^<version^>    Set version ^(e.g., 0.1.0^)
echo   bump ^<type^>      Bump version ^(major^|minor^|patch^)
echo   sync             Sync version to package.json
echo   sync-docs        Detect version from installer files and update docs\index.html
exit /b 1

REM ===================================
REM Helper Functions
REM ===================================

:get_current_version
REM Read version from VERSION file
if exist "%VERSION_FILE%" (
    set /p VERSION=<"%VERSION_FILE%"
    REM Trim whitespace
    for /f "tokens=* delims= " %%a in ("!VERSION!") do set "VERSION=%%a"
    set "%~1=!VERSION!"
) else (
    set "%~1=0.0.0"
)
goto :eof

:sync_to_package_json
set "VERSION_TO_SYNC=%~1"
if "%VERSION_TO_SYNC%"=="" call :get_current_version VERSION_TO_SYNC

if exist "%PACKAGE_JSON%" (
    REM Use Node.js to update package.json (more reliable for JSON)
    where node >nul 2>&1
    if not errorlevel 1 (
        node -e "const fs = require('fs'); const pkg = JSON.parse(fs.readFileSync('%PACKAGE_JSON%', 'utf8')); pkg.version = '%VERSION_TO_SYNC%'; fs.writeFileSync('%PACKAGE_JSON%', JSON.stringify(pkg, null, 2) + '\n');"
        echo Synced version to frontend\package.json
    ) else (
        echo Warning: node not found, skipping package.json sync
    )
)
goto :eof

