============================================================
CAPM & GORDON MODEL STOCK VALUATION CALCULATOR
============================================================

HOW TO RUN:
-----------
Just double-click: START.bat

That's it! The calculator will open in your browser automatically.


IMPORTANT FILES:
----------------
START.bat                  - MAIN LAUNCHER (use this!)
backend_tradingview.py     - Backend server (TradingView data - RECOMMENDED)
index.html                 - Frontend interface

ALTERNATIVE BACKENDS (if TradingView doesn't work):
---------------------------------------------------
backend_vnstock.py         - Uses vnstock for VN stocks (less accurate beta)
backend_claude.py          - Uses Claude AI (requires API credits)

To use alternative backends, edit START.bat and change:
  python -u backend_tradingview.py
to:
  python -u backend_vnstock.py
or:
  python -u backend_claude.py


FEATURES:
---------
- FREE - No API credits needed (TradingView backend)
- Accurate beta values from TradingView
- Real dividend data for Vietnamese stocks
- Supports both Vietnamese (VNM, VCB, FPT, etc.) and US stocks (AAPL, MSFT, etc.)
- CAPM vs Gordon Model comparison
- Automatic valuation (UNDERVALUED/OVERVALUED/FAIR)


SUPPORTED VIETNAMESE STOCKS:
----------------------------
VNM, VCB, FPT, HPG, VHM, VIC, MSN, VRE, TCB, BVH, GAS, MWG,
PLX, POW, SAB, SSI, VJC, VPB, CTG, BID, MBB, ACB, HDB, NVL,
VCI, PDR, VND, KDH, DIG, GEX


TROUBLESHOOTING:
----------------
If the app doesn't open automatically:
1. Make sure START.bat is running
2. Manually open index.html in your browser
3. Wait a few seconds for the backend to fully start

If you get errors:
1. Make sure Python is installed
2. Run: SETUP_TRADINGVIEW.bat (installs required packages)


CURRENT SETTINGS:
-----------------
- Vietnam risk-free rate: 4.16% (10-year gov bond, Jan 2026)
- Vietnam market return: 9% (VN-Index historical)
- US risk-free rate: 4.2% (10-year Treasury)
- US market return: 10% (S&P 500 historical)


============================================================
Generated with Claude Code
============================================================
