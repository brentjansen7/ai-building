@echo off
REM AI Arbitrage System - Windows Setup Launcher
REM Right-click this file → Run as administrator

echo.
echo ========== AI Arbitrage System Setup ==========
echo.
echo Running PowerShell setup script...
echo (If prompted, click "Yes" to allow execution)
echo.

REM Run PowerShell with the setup script
powershell -ExecutionPolicy Bypass -File "SETUP_WINDOWS.ps1"

REM Keep window open to see output
pause
