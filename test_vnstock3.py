# -*- coding: utf-8 -*-
"""
Test vnstock to see column names
"""
import sys
import io

# Redirect stdout/stderr temporarily
original_stdout = sys.stdout
original_stderr = sys.stderr

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')

    from vnstock import Finance

    sys.stdout = original_stdout
    sys.stderr = original_stderr

    ticker = 'VNM'
    finance = Finance(source="VCI", symbol=ticker, period="year")
    ratios = finance.ratio(symbol=ticker, period="year", flatten_columns=True, separator="_")

    # Save columns to file
    with open('vnstock_columns.txt', 'w', encoding='utf-8') as f:
        for col in ratios.columns:
            f.write(f"{col}\n")

    print(f"Saved {len(ratios.columns)} column names to vnstock_columns.txt")

    # Also show first row data
    if not ratios.empty:
        with open('vnstock_first_row.txt', 'w', encoding='utf-8') as f:
            latest = ratios.iloc[0]
            for col in ratios.columns:
                f.write(f"{col}: {latest[col]}\n")

        print(f"Saved first row data to vnstock_first_row.txt")

except Exception as e:
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
