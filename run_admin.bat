@echo off
REM Automated Lo-Fi YouTube Channel Generator - Admin Launcher
REM This script runs the automation in administrator mode to ensure proper wake lock functionality

echo ========================================
echo Lo-Fi Automation - Admin Mode Launcher
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires administrator privileges.
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running with administrator privileges
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.11+ or add it to your PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if dependencies are installed
python -c "import dotenv" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Dependencies not installed
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed
echo.

REM Run the automation
echo Starting Lo-Fi Automation...
echo.
echo ========================================
echo.

python runner.py %*

echo.
echo ========================================
echo Automation finished
echo ========================================
pause

