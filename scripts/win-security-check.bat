@echo off
REM Security Check Script for Windows
REM Scans Python and Node.js dependencies for known vulnerabilities

setlocal enabledelayedexpansion

set VULN_FOUND=0

echo.
echo ================================================================================
echo Security Vulnerability Scan
echo ================================================================================
echo.

REM Check Python dependencies
echo ================================================================================
echo Python Dependencies Scan
echo ================================================================================

if not exist "backend\requirements.txt" (
    echo [WARNING] backend\requirements.txt not found. Skipping Python scan.
    goto :nodejs_scan
)

REM Check if pip-audit is installed
pip-audit --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] pip-audit not found. Installing...
    pip install --upgrade pip
    pip install pip-audit^>=2.6.0
)

cd backend
pip-audit --requirement requirements.txt
if errorlevel 1 (
    echo [ERROR] Python vulnerabilities detected!
    set VULN_FOUND=1
) else (
    echo [SUCCESS] No Python vulnerabilities found
)
cd ..

:nodejs_scan
echo.
echo ================================================================================
echo Node.js Dependencies Scan
echo ================================================================================

if not exist "frontend\package.json" (
    echo [WARNING] frontend\package.json not found. Skipping Node.js scan.
    goto :summary
)

cd frontend

REM Check if node_modules exists, if not, install dependencies
if not exist "node_modules" (
    echo [INFO] node_modules not found. Installing dependencies...
    call npm install
)

REM Run npm audit
call npm audit --audit-level=moderate
if errorlevel 1 (
    echo [ERROR] Node.js vulnerabilities detected!
    set VULN_FOUND=1
) else (
    echo [SUCCESS] No Node.js vulnerabilities found
)
cd ..

:summary
echo.
echo ================================================================================

if %VULN_FOUND%==0 (
    echo [SUCCESS] Security scan completed: No vulnerabilities found
    exit /b 0
) else (
    echo [ERROR] Security scan completed: Vulnerabilities detected
    echo.
    echo To fix vulnerabilities:
    echo   Python: Review pip-audit output and update packages in backend\requirements.txt
    echo   Node.js: Run 'npm audit fix' in frontend\ directory (or update packages manually)
    exit /b 1
)
