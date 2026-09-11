@echo off
REM AI Arbitrage System - Start All Services
REM This opens 2 PowerShell windows for API and Worker

echo.
echo ========== Starting AI Arbitrage System ==========
echo.
echo Opening API Server (Window 1)...
start powershell -NoExit -Command "cd '%CD%'; .\venv\Scripts\activate; uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo Opening Scraper Worker (Window 2)...
timeout /t 2 /nobreak
start powershell -NoExit -Command "cd '%CD%'; .\venv\Scripts\activate; arq scraper.tasks.WorkerSettings"

echo.
echo ========== System Starting ==========
echo.
echo API: http://localhost:8000
echo Health: http://localhost:8000/health
echo.
echo Next:
echo 1. Open Chrome
echo 2. Go to chrome://extensions
echo 3. Enable "Developer mode"
echo 4. Click "Load unpacked"
echo 5. Select extension folder
echo 6. Visit marktplaats.nl
echo.
echo Press any key to close this window...
pause
