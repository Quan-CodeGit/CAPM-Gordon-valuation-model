@echo off
title CAPM Calculator - Starting...
color 0A

echo ============================================================
echo    CAPM ^& Gordon Model Stock Valuation Calculator
echo ============================================================
echo.
echo [1/3] Cleaning up any existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 2^>nul') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do taskkill /F /PID %%a 2>nul
timeout /t 1 /nobreak >nul

echo [2/3] Starting Backend Server (Flask API)...
start "CAPM Backend" /MIN cmd /c "python backend_tradingview.py"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Server...
start "CAPM Frontend" /MIN cmd /c "python -m http.server 8000"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo    SUCCESS! Your calculator is ready!
echo ============================================================
echo.
echo Opening browser in 3 seconds...
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:8000
echo.
echo IMPORTANT: Do NOT close this window while using the app!
echo            Press any key to stop the servers and exit.
echo ============================================================
timeout /t 3 /nobreak >nul

start http://localhost:8000

echo.
echo Calculator is running... Press any key to stop servers.
pause >nul

echo.
echo Stopping servers...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 2^>nul') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do taskkill /F /PID %%a 2>nul

echo Servers stopped. Goodbye!
timeout /t 2 /nobreak >nul
