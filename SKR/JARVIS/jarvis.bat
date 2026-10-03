@echo off
title JARVIS - Just A Rather Very Intelligent System
color 0B

echo.
echo  =====================================
echo   J.A.R.V.I.S  -  Starting up...
echo  =====================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check .env
if not exist .env (
    echo  No .env found. Running setup...
    python main.py --setup
    echo.
)

:: Launch JARVIS
python main.py %*
pause
