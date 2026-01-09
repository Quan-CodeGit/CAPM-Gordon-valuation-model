# -*- coding: utf-8 -*-
"""
Test vnstock library for Vietnamese stock data
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from vnstock import *
    print("Testing vnstock library...")

    # Test getting financial ratios for VNM
    ticker = 'VNM'
    print(f"\nFetching data for {ticker}...")

    # Try to get financial ratios
    try:
        # Method 1: Try financial_ratio function
        ratios = financial_ratio(symbol=ticker, mode='simplify', missing_pct=0.8)
        print("\n=== Financial Ratios ===")
        print(ratios)
    except Exception as e:
        print(f"Method 1 failed: {e}")

    # Try to get company overview/fundamental data
    try:
        # Method 2: Try company overview
        overview = company_overview(ticker)
        print("\n=== Company Overview ===")
        print(overview)
    except Exception as e:
        print(f"Method 2 failed: {e}")

    # Try listing available functions
    print("\n=== Available functions ===")
    import vnstock
    funcs = [f for f in dir(vnstock) if not f.startswith('_')]
    for func in funcs[:20]:  # Show first 20
        print(f"  - {func}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
