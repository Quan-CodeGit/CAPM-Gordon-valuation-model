@echo off
echo ============================================================
echo CAPM Calculator - DAMODARAN METHOD
echo ============================================================
echo.
echo This version uses Damodaran's Country Risk Premium methodology
echo Data source: NYU Stern (January 5, 2026)
echo.
echo Country Risk Premiums:
echo   Vietnam (Ba2):   8.13%% Total ERP
echo   Australia (Aaa): 4.23%% Total ERP
echo   US (Aa1):        4.46%% Total ERP
echo.
echo ============================================================
echo Starting backend on port 5001...
echo ============================================================

python backend_damodaran.py

pause
