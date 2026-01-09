@echo off
echo ============================================================
echo CAPM ^& Gordon Model Calculator - EASY START
echo ============================================================
echo.
echo Starting backend server...
echo.

REM Kill any existing Python processes running the backend
taskkill /F /IM python.exe 2>nul

REM Start backend in background
start /B python -u backend_tradingview.py

REM Wait 5 seconds for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Open frontend in default browser
echo Opening calculator in your browser...
start index.html

echo.
echo ============================================================
echo Calculator is now running!
echo ============================================================
echo.
echo The app should open in your browser automatically.
echo If not, open this file manually: index.html
echo.
echo Press Ctrl+C to stop the backend server when done.
echo ============================================================
echo.

REM Keep backend running
python -u backend_tradingview.py
