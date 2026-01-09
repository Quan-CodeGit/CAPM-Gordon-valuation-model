# -*- coding: utf-8 -*-
"""
Test vnstock library - suppress emoji errors
"""
import sys
import io

# Redirect stdout/stderr temporarily to bypass emoji encoding issues
original_stdout = sys.stdout
original_stderr = sys.stderr

try:
    # Use UTF-8 encoding
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')

    from vnstock import Finance

    # Restore stdout/stderr
    sys.stdout = original_stdout
    sys.stderr = original_stderr

    print("[OK] vnstock loaded successfully!")

    # Test getting financial ratios for VNM and PLX
    for ticker in ['VNM', 'PLX']:
        print(f"\n{'='*60}")
        print(f"Testing financial data for {ticker}")
        print('='*60)

        try:
            # Initialize Finance object
            finance = Finance(source="VCI", symbol=ticker, period="year")

            # Get financial ratios
            ratios = finance.ratio(symbol=ticker, period="year", flatten_columns=True, separator="_")

            # Get latest data (most recent row)
            if not ratios.empty:
                print(f"Fetched {len(ratios)} rows of data")
                latest = ratios.iloc[0]  # Most recent data is usually first row

                # Extract P/E, ROE, EPS
                pe = None
                roe = None
                eps = None

                # Try different column name variations (skip printing column names with Vietnamese)
                for col in ratios.columns:
                    try:
                        col_lower = col.lower()
                        if 'pe' in col_lower or 'pricetoearning' in col_lower:
                            pe = latest[col]
                        elif 'roe' in col_lower or 'returnonequity' in col_lower:
                            roe = latest[col]
                        elif 'eps' in col_lower or 'earningpershare' in col_lower:
                            eps = latest[col]
                    except:
                        pass  # Skip Vietnamese characters

                print(f"\n=== Summary for {ticker} ===")
                print(f"EPS: {eps}")
                print(f"P/E: {pe}")
                print(f"ROE: {roe}")
            else:
                print("No data returned")

        except Exception as e:
            print(f"Error getting financial ratios for {ticker}: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
