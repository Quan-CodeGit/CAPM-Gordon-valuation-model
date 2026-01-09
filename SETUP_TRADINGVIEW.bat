@echo off
title Setup TradingView Backend
color 0B

echo ========================================
echo  TradingView Backend Setup
echo ========================================
echo.
echo This will install tradingview-scraper
echo for FREE, accurate stock data!
echo.
echo Features:
echo   - Real beta from TradingView
echo   - No API key needed
echo   - Completely FREE
echo.
pause

cd /d "%~dp0"

echo.
echo Installing tradingview-scraper...
pip install tradingview-scraper

echo.
echo Testing installation...
python -c "from tradingview_scraper.symbols.overview import Overview; print('Success! TradingView scraper is ready')"

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next step: Run START_APP_TRADINGVIEW.bat
echo.
pause
