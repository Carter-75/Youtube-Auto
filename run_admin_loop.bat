@echo off
REM Automated Lo-Fi YouTube Channel Generator - Admin Launcher with Loop
REM This script runs the automation in administrator mode with batch generation

echo ========================================
echo Lo-Fi Automation - Batch Mode (Admin)
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

REM Prompt for number of videos
set /p VIDEO_COUNT="How many videos to generate? (default: 5): "
if "%VIDEO_COUNT%"=="" set VIDEO_COUNT=5

REM Prompt for delay
set /p DELAY_SECONDS="Delay between videos in seconds? (default: 60): "
if "%DELAY_SECONDS%"=="" set DELAY_SECONDS=60

echo.
echo Configuration:
echo - Videos to generate: %VIDEO_COUNT%
echo - Delay between videos: %DELAY_SECONDS% seconds
echo - System will stay awake during generation
echo - System can sleep during delays
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting batch generation...
echo.
echo ========================================
echo.

cd src
python main.py --loop %VIDEO_COUNT% %DELAY_SECONDS%

echo.
echo ========================================
echo Batch generation finished
echo ========================================
pause

