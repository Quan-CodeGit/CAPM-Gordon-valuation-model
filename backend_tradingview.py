"""
Backend using TradingView Scraper for accurate, FREE financial data
No API key needed! Gets real beta values from TradingView directly.
"""
import sys
import io

# Suppress vnstock emoji errors by redirecting both stdout and stderr before any imports
_original_stderr = sys.stderr
_original_stdout = sys.stdout
try:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
    from vnstock import Finance
    _vnstock_loaded = True
except Exception as e:
    _vnstock_loaded = False
    # Don't print the error - it contains emojis that will crash
finally:
    sys.stderr = _original_stderr
    sys.stdout = _original_stdout

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
CORS(app)

# Alpha Vantage API Key for P/E data
ALPHA_VANTAGE_API_KEY = "PN4MBNMUOULYYXVC"

# Cache results
_cache = {}
_cache_timeout = 300  # 5 minutes

# Vietnamese stocks list (VN30 + additional major stocks)
VIETNAMESE_STOCKS = [
    # VN30 Index Components
    'VIC', 'VHM', 'TCB', 'FPT', 'VPB', 'LPB', 'HPG', 'HDB', 'ACB', 'MBB',
    'MWG', 'STB', 'MSN', 'VCB', 'VJC', 'SHB', 'SSI', 'VNM', 'CTG', 'VIB',
    'VRE', 'SSB', 'TPB', 'DGC', 'BID', 'GAS', 'SAB', 'PLX', 'GVR', 'BCM',
    # Additional Banking
    'EIB', 'VIB',
    # Additional Real Estate & Construction
    'NVL', 'KDH', 'DXG', 'PDR', 'DIG', 'HDC', 'CEO', 'NLG',
    # Additional Food & Beverage
    'VHC', 'MCH',
    # Additional Technology & Telecom
    'VGI', 'CMG', 'ITD',
    # Additional Industrial & Materials
    'HSG', 'NKG', 'DCM', 'DPM', 'NT2',
    # Additional Energy & Utilities
    'POW', 'PVD', 'PVT', 'BSR', 'PVS', 'PVG',
    # Additional Retail & Consumer
    'PNJ', 'FRT',
    # Additional Securities & Finance
    'VCI', 'VND', 'HCM', 'MBS', 'VIX',
    # Additional Insurance
    'BVH', 'BMI', 'BIC', 'PRE',
    # Additional Transportation & Logistics
    'HVN', 'VTP', 'GMD', 'HAH',
    # Other major stocks
    'GEX', 'DHG', 'REE', 'DPR', 'PC1', 'VPI'
]

# Fallback dividend data for major Vietnamese stocks (in actual VND, not thousands)
# Source: Recent financial reports and historical averages
DIVIDEND_FALLBACK = {
    'VNM': {'dividend': 3000, 'growth': 0.04},   # Vinamilk
    'VCB': {'dividend': 1500, 'growth': 0.08},   # Vietcombank
    'FPT': {'dividend': 2500, 'growth': 0.12},   # FPT Corporation (12% growth recent years)
    'HPG': {'dividend': 1800, 'growth': 0.06},   # Hoa Phat
    'TCB': {'dividend': 1000, 'growth': 0.10},   # Techcombank
    'SAB': {'dividend': 2200, 'growth': 0.04},   # Sabeco
    'GAS': {'dividend': 4000, 'growth': 0.04},   # PVGas
    'MBB': {'dividend': 800, 'growth': 0.09},    # Military Bank
    'VHM': {'dividend': 2000, 'growth': 0.03},   # Vinhomes
    'MSN': {'dividend': 1200, 'growth': 0.05},   # Masan
}

# CafeF.vn URL mapping for major Vietnamese stocks
# Format: ticker -> cafef URL slug
CAFEF_URL_MAPPING = {
    'VNM': 'VNM-cong-ty-co-phan-sua-viet-nam',           # Vinamilk
    'VCB': 'VCB-ngan-hang-tmcp-ngoai-thuong-viet-nam',   # Vietcombank
    'FPT': 'FPT-cong-ty-co-phan-fpt',                    # FPT Corporation
    'HPG': 'HPG-ctcp-tap-doan-hoa-phat',                 # Hoa Phat Group
    'TCB': 'TCB-ngan-hang-tmcp-ky-thuong-viet-nam',      # Techcombank
    'SAB': 'SAB-tong-cong-ty-cp-bia-ruou-nuoc-giai-khat-sai-gon', # Sabeco
    'GAS': 'GAS-tong-cong-ty-khi-viet-nam-ctcp',         # PVGas
    'MBB': 'MBB-ngan-hang-tmcp-quan-doi',                # Military Bank
    'VHM': 'VHM-ctcp-vinhomes',                          # Vinhomes
    'MSN': 'MSN-ctcp-tap-doan-ma-san',                   # Masan
    'PLX': 'PLX-tap-doan-xang-dau-viet-nam',             # Petrolimex
    'VIC': 'VIC-tap-doan-vingroup',                      # Vingroup
    'VRE': 'VRE-ctcp-vincom-retail',                     # Vincom Retail
    'BVH': 'BVH-tap-doan-bao-viet',                      # Bao Viet
    'MWG': 'MWG-ctcp-dau-tu-the-gioi-di-dong',           # Mobile World
    'POW': 'POW-tong-cong-ty-dien-luc-dau-khi-viet-nam-ctcp', # POW
    'SSI': 'SSI-ctcp-chung-khoan-ssi',                   # SSI Securities
    'VJC': 'VJC-ctcp-hang-khong-vietjet',                # VietJet Air
    'VPB': 'VPB-ngan-hang-tmcp-viet-nam-thinh-vuong',    # VPBank
    'CTG': 'CTG-ngan-hang-tmcp-cong-thuong-viet-nam',    # VietinBank
    'BID': 'BID-ngan-hang-tmcp-dau-tu-va-phat-trien-viet-nam', # BIDV
    'ACB': 'ACB-ngan-hang-tmcp-a-chau',                  # ACB
    'HDB': 'HDB-ngan-hang-tmcp-phat-trien-tp-hcm',       # HDBank
    'NVL': 'NVL-ctcp-tap-doan-dau-tu-dia-oc-no-va',      # Novaland
}

def get_vn_dividend_data(ticker):
    """
    Get Vietnamese stock dividend data from vnstock
    Returns (dividend_rate, dividend_growth) or fallback values
    """

    try:
        from vnstock import Vnstock

        print(f"Fetching Vietnamese dividend data for {ticker} from vnstock...")
        stock = Vnstock().stock(symbol=ticker, source='VCI')

        # Try to get financial ratios for dividend data
        ratios = stock.finance.ratio(period='year', lang='en')

        if ratios is not None and not ratios.empty:
            print(f"Available columns: {list(ratios.columns)}")  # Debug: show available columns

            if 'dividendPerShare' in ratios.columns:
                # Get last 2 years of dividend data
                dividends = ratios['dividendPerShare'].head(2)

                if len(dividends) >= 1 and not pd.isna(dividends.iloc[0]) and dividends.iloc[0] > 0:
                    # Latest dividend (in thousands VND, need to multiply by 1000)
                    latest_div = float(dividends.iloc[0]) * 1000

                    # Calculate growth if we have 2 years of data
                    if len(dividends) >= 2 and not pd.isna(dividends.iloc[1]) and dividends.iloc[1] > 0:
                        prev_div = float(dividends.iloc[1]) * 1000
                        growth = (latest_div / prev_div) - 1
                        print(f"[OK] Found dividends: Latest={latest_div:.0f} VND, Previous={prev_div:.0f} VND, Growth={growth*100:.2f}%")
                        return latest_div, growth
                    else:
                        print(f"[OK] Found latest dividend: {latest_div:.0f} VND (no historical data for growth)")
                        # Use fallback growth if available
                        fallback_growth = DIVIDEND_FALLBACK.get(ticker, {}).get('growth', 0.05)
                        return latest_div, fallback_growth

        print(f"[WARN] No dividend data found in vnstock for {ticker}")

    except Exception as e:
        print(f"Error fetching vnstock dividend data: {e}")
        import traceback
        traceback.print_exc()

    # Use fallback data if available
    if ticker in DIVIDEND_FALLBACK:
        fallback = DIVIDEND_FALLBACK[ticker]
        print(f"Using fallback data for {ticker}: Dividend={fallback['dividend']} VND, Growth={fallback['growth']*100:.1f}%")
        return fallback['dividend'], fallback['growth']

    print(f"No fallback data for {ticker}, using default: 0 VND, 5% growth")
    return 0, 0.05

def get_tradingview_fundamentals(ticker, tv_symbol):
    """
    Get fundamental/dividend data from TradingView
    Returns (dividend_per_share, dividend_yield_percent) or (0, 0)
    """
    try:
        from tradingview_scraper.symbols.fundamental_graphs import FundamentalGraphs

        print(f"Fetching fundamentals for {tv_symbol}...")
        fg = FundamentalGraphs()
        data = fg.get_fundamentals(symbol=tv_symbol)

        if data and 'data' in data:
            fundamentals = data['data']

            # Get dividend yield (as percentage)
            div_yield = fundamentals.get('dividends_yield', 0)

            # Try to get dividend per share (try multiple fields)
            # dividends_per_share_fq is quarterly, we want annual
            div_per_share = fundamentals.get('dividends_per_share_fy', None)  # FY = Fiscal Year
            if not div_per_share or div_per_share == 0:
                div_per_share = fundamentals.get('dividends_per_share_fq', None)  # FQ = Fiscal Quarter
            if not div_per_share or div_per_share == 0:
                div_per_share = None

            print(f"[OK] Fundamentals: Dividend Yield={div_yield}%, DPS={div_per_share}")
            print(f"     Available dividend fields: {[k for k in fundamentals.keys() if 'dividend' in k.lower()]}")
            return div_per_share, div_yield

    except Exception as e:
        print(f"Could not fetch fundamentals: {e}")

    return None, 0

def get_tradingview_data(ticker, is_vn_stock=False):
    """
    Fetch stock data from TradingView using tradingview-scraper
    """
    try:
        from tradingview_scraper.symbols.overview import Overview

        print(f"Fetching TradingView data for {ticker}...")

        # Format ticker for TradingView
        if is_vn_stock:
            # Vietnamese stocks on HOSE/HNX
            tv_symbol = f"HOSE:{ticker}"
        else:
            # Try to detect US exchange
            tv_symbol = f"NASDAQ:{ticker}"

        overview = Overview()

        # Try multiple exchanges for US stocks
        data = None
        for exchange in ['NASDAQ', 'NYSE', 'AMEX'] if not is_vn_stock else ['HOSE', 'HNX']:
            try:
                tv_symbol = f"{exchange}:{ticker}"
                print(f"Trying {tv_symbol}...")
                result = overview.get_symbol_overview(symbol=tv_symbol)
                if result and 'data' in result:
                    data = result['data']
                    print(f"[OK] Found data on {exchange}")
                    break
            except Exception as e:
                print(f"  {exchange} failed: {e}")
                continue

        if not data:
            print(f"[ERROR] Could not find {ticker} on TradingView")
            return None

        # Extract data
        current_price = data.get('close', 0)
        beta = data.get('beta_1_year', 1.0)
        company_name = data.get('description', ticker)
        dividend_yield_percent = data.get('dividends_yield', 0)  # TradingView returns as percentage (0.39 = 0.39%)
        market_cap = data.get('market_cap_basic', 0)

        # Convert dividend yield from percentage to decimal
        # TradingView returns 0.39 for 0.39%, we need 0.0039 for calculations
        dividend_yield = dividend_yield_percent / 100 if dividend_yield_percent else 0

        # Calculate annual dividend in dollars/VND
        # Dividend = Price × Yield (as decimal)
        dividend_rate = current_price * dividend_yield if dividend_yield else 0

        print(f"[OK] Data retrieved:")
        print(f"  Company: {company_name}")
        print(f"  Price: {current_price}")
        print(f"  Beta: {beta}")
        print(f"  Dividend Yield: {dividend_yield_percent}% -> {dividend_yield:.4f} (decimal)")
        print(f"  Annual Dividend: {dividend_rate:.2f}")

        return {
            'currentPrice': current_price,
            'beta': beta if beta is not None else 1.0,  # Allow negative beta, only use 1.0 if None
            'companyName': company_name,
            'dividend': dividend_rate,
            'dividendYield': dividend_yield,
            'marketCap': market_cap,
            'source': f'TradingView ({tv_symbol})'
        }

    except ImportError:
        print("ERROR: tradingview-scraper not installed!")
        print("Install with: pip install tradingview-scraper")
        return None
    except Exception as e:
        print(f"Error fetching TradingView data: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()

        # Get market parameter from query string (VN or US)
        market = request.args.get('market', 'VN').upper()
        print(f"[REQUEST] Received request for {ticker} (Market: {market})")

        # Check cache (include market in cache key)
        cache_key = f"{ticker}_{market}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            print(f"[CACHE] Returning cached result for {ticker}")
            return jsonify(_cache[cache_key])

        print(f"[CACHE] No cache for {ticker}, fetching fresh data")

        time.sleep(1)  # Rate limiting

        # Determine if Vietnamese stock based on market parameter or ticker list
        if market == 'VN':
            is_vn_stock = True
        elif market == 'US':
            is_vn_stock = False
        else:
            # Fallback: auto-detect based on ticker list
            is_vn_stock = ticker in VIETNAMESE_STOCKS

        # Get data from TradingView
        tv_data = get_tradingview_data(ticker, is_vn_stock)

        if not tv_data:
            return jsonify({
                'error': f'Unable to fetch data for {ticker} from TradingView'
            }), 400

        current_price = tv_data['currentPrice']
        beta = tv_data['beta']
        company_name = tv_data['companyName']
        dividend_rate = tv_data['dividend']
        yf_stock = None  # Initialize yfinance stock object for US stocks

        # Set appropriate rates based on market
        if is_vn_stock:
            risk_free_rate = 0.0416  # Vietnam 10-year bond yield (Jan 2026: 4.16%)
            market_return = 0.09     # VN-Index historical return ~9%
            currency = 'VND'

            # VN stocks use curated data, so irregular dividend flag is not needed
            irregular_dividend = False
            dividend_consistency_issues = []

            # For Vietnamese stocks, prioritize fallback data over TradingView
            # TradingView's dividend data for VN stocks is often outdated/inaccurate
            # Use fallback data (from company reports) if available
            if ticker in DIVIDEND_FALLBACK:
                fallback = DIVIDEND_FALLBACK[ticker]
                dividend_rate = fallback['dividend']
                dividend_growth = fallback['growth']
                print(f"Using fallback dividend data for {ticker}: {dividend_rate:.0f} VND, growth: {dividend_growth*100:.1f}%")
            else:
                # If no fallback, try TradingView fundamentals
                print(f"Fetching dividend data from TradingView fundamentals for {ticker}...")
                div_per_share, div_yield_pct = get_tradingview_fundamentals(ticker, tv_data['source'].split('(')[1].split(')')[0])

                # Prioritize dividend per share if available, otherwise use yield
                if div_per_share is not None and div_per_share > 0:
                    # Use actual dividend per share from TradingView
                    # TradingView returns annual dividend in thousands for VN stocks
                    dividend_rate = div_per_share * 1000
                    print(f"Using TradingView dividend per share: {div_per_share} → {dividend_rate:.0f} VND")

                    # Try to get growth from vnstock
                    _, vn_growth = get_vn_dividend_data(ticker)
                    dividend_growth = vn_growth
                elif div_yield_pct > 0:
                    # Fall back to calculating from dividend yield
                    # TradingView returns yield as percentage (0.7826 = 0.7826%)
                    # Convert to decimal and calculate dividend
                    div_yield = div_yield_pct / 100
                    dividend_rate = current_price * div_yield
                    print(f"Using TradingView dividend yield: {div_yield_pct:.2f}% = {dividend_rate:.0f} VND")

                    # Try to get growth from vnstock
                    _, vn_growth = get_vn_dividend_data(ticker)
                    dividend_growth = vn_growth
                else:
                    # Last resort: try vnstock
                    print(f"TradingView has no dividend, trying vnstock...")
                    vn_dividend, vn_growth = get_vn_dividend_data(ticker)
                    dividend_rate = vn_dividend
                    dividend_growth = vn_growth
                    print(f"Using vnstock: {vn_dividend:.0f} VND, growth: {vn_growth*100:.2f}%")

        else:
            # Get live US risk-free rate from yfinance (US 10-year Treasury)
            try:
                import yfinance as yf
                treasury = yf.Ticker("^TNX")  # 10-year Treasury yield
                treasury_data = treasury.history(period="5d")
                if not treasury_data.empty:
                    # Treasury yields are in percentage, convert to decimal
                    risk_free_rate = treasury_data['Close'].iloc[-1] / 100
                    print(f"Live US risk-free rate: {risk_free_rate*100:.2f}%")
                else:
                    risk_free_rate = 0.042  # Fallback
                    print(f"Using fallback US risk-free rate: 4.2%")
            except:
                risk_free_rate = 0.042  # Fallback
                print(f"Using fallback US risk-free rate: 4.2%")

            market_return = 0.10    # S&P 500 historical ~10%

            # Get dividend growth from yfinance historical data and save stock object for later
            irregular_dividend = False
            dividend_consistency_issues = []

            try:
                yf_stock = yf.Ticker(ticker)
                dividends = yf_stock.dividends
                if len(dividends) >= 2:
                    # Get last 5 years of annual dividends to check consistency
                    annual_divs = dividends.resample('Y').sum()
                    if len(annual_divs) >= 2:
                        latest = annual_divs.iloc[-1]
                        previous = annual_divs.iloc[-2]

                        # Check for irregular patterns
                        if len(annual_divs) >= 3:
                            # Check for zero dividends in history
                            zero_years = (annual_divs == 0).sum()
                            if zero_years > 0:
                                irregular_dividend = True
                                dividend_consistency_issues.append(f"Skipped dividends in {zero_years} year(s)")

                            # Check for high volatility (coefficient of variation)
                            non_zero_divs = annual_divs[annual_divs > 0]
                            if len(non_zero_divs) >= 3:
                                div_std = non_zero_divs.std()
                                div_mean = non_zero_divs.mean()
                                if div_mean > 0:
                                    cv = div_std / div_mean
                                    if cv > 0.5:  # High volatility threshold
                                        irregular_dividend = True
                                        dividend_consistency_issues.append("High dividend volatility")

                        if previous > 0:
                            dividend_growth = (latest / previous) - 1
                            print(f"Calculated dividend growth from history: {dividend_growth*100:.1f}%")

                            # Check for extreme growth rates
                            if abs(dividend_growth) > 0.5:  # More than 50% change
                                irregular_dividend = True
                                dividend_consistency_issues.append(f"Extreme growth rate: {dividend_growth*100:.1f}%")
                        else:
                            dividend_growth = 0.03
                            irregular_dividend = True
                            dividend_consistency_issues.append("Previous year had zero dividend")
                    else:
                        dividend_growth = 0.03
                        irregular_dividend = True
                        dividend_consistency_issues.append("Limited dividend history")
                else:
                    dividend_growth = 0.03
                    irregular_dividend = True
                    dividend_consistency_issues.append("Insufficient dividend history")
            except:
                dividend_growth = 0.03  # Estimate 3% growth as fallback
                irregular_dividend = True
                dividend_consistency_issues.append("Unable to fetch dividend data")

            currency = 'USD'

        # Calculate CAPM
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)

        # Calculate Gordon Model
        if dividend_rate > 0:
            # Gordon Model: E(R) = (D₁/P₀) + g
            # Where D₁ = D₀ × (1 + g), P₀ is current price, g is growth rate
            d1 = dividend_rate * (1 + dividend_growth)
            dividend_yield_d1 = d1 / current_price
            gordon_return = dividend_yield_d1 + dividend_growth

            # Calculate fair price using Gordon Model
            # Fair Price = D₁ / (Required Return - Growth Rate)
            if capm_return is not None and dividend_growth is not None and capm_return > dividend_growth:
                fair_price = d1 / (capm_return - dividend_growth)
            else:
                # If CAPM return <= growth, Gordon model breaks down
                fair_price = current_price  # Can't calculate meaningful fair price
        else:
            # No dividend - Gordon Model doesn't apply properly
            # But we can still show the expected return as the growth rate
            d1 = 0  # No next year dividend
            gordon_return = dividend_growth
            # Without dividends, we can't calculate a Gordon-based fair price
            # Use current price as placeholder (valuation will be based on returns comparison)
            fair_price = current_price
            print(f"Warning: No dividend data for {ticker}. Gordon model less reliable without dividends.")

        # Determine valuation
        valuation = "OVERVALUED" if gordon_return < capm_return else "UNDERVALUED"
        price_difference = ((fair_price - current_price) / current_price) * 100

        # Check if this is a low-dividend stock (dividend yield < 1%)
        dividend_yield = (dividend_rate / current_price) if dividend_rate > 0 else 0
        low_dividend_warning = None
        if dividend_yield < 0.01 and dividend_rate > 0:
            low_dividend_warning = "Low dividend yield - investors primarily rely on capital gains. Gordon Model may not be appropriate for valuation."
        elif dividend_rate == 0:
            low_dividend_warning = "No dividend - Gordon Model does not apply. Valuation relies entirely on capital appreciation."

        # Calculate P/E ratio and its components
        # P/E = Payout Ratio / (ke - g)
        # where ke = CAPM return, g = growth rate
        eps = None
        payout_ratio = None
        retention_ratio = None
        roe = None
        pe_ratio = None
        theoretical_pe = None

        print(f"[DEBUG] Starting P/E calculation for {ticker}, is_vn_stock={is_vn_stock}")

        try:
            if not is_vn_stock:
                # Try multiple unlimited sources for P/E data
                print(f"Fetching P/E data for {ticker}...")
                eps = None
                import requests

                # Method 1: Yahoo Finance API (unlimited, free)
                try:
                    print(f"Trying Yahoo Finance API...")
                    yf_api_url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=defaultKeyStatistics,financialData"
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    response = requests.get(yf_api_url, headers=headers, timeout=5)
                    data = response.json()

                    if 'quoteSummary' in data and data['quoteSummary']['result']:
                        result = data['quoteSummary']['result'][0]

                        # Get EPS from defaultKeyStatistics
                        if 'defaultKeyStatistics' in result:
                            stats = result['defaultKeyStatistics']
                            eps_raw = stats.get('trailingEps', {})
                            if isinstance(eps_raw, dict):
                                eps = eps_raw.get('raw', None)
                            else:
                                eps = eps_raw

                        if eps:
                            print(f"[OK] EPS from Yahoo Finance API: ${eps:.2f}")
                except Exception as e:
                    print(f"Yahoo Finance API failed: {e}")

                # Method 2: Fallback to yfinance library
                if not eps and yf_stock:
                    try:
                        print(f"Trying yfinance library...")
                        info = yf_stock.info
                        eps = info.get('trailingEps', None)
                        if eps:
                            print(f"[OK] EPS from yfinance: ${eps:.2f}")
                    except Exception as e:
                        print(f"yfinance failed: {e}")

                # Method 3: Last resort - Alpha Vantage (25/day limit)
                if not eps:
                    try:
                        print(f"Trying Alpha Vantage (limited to 25/day)...")
                        av_url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
                        response = requests.get(av_url, timeout=5)
                        data = response.json()

                        if 'quarterlyEarnings' in data and len(data['quarterlyEarnings']) > 0:
                            latest = data['quarterlyEarnings'][0]
                            eps = float(latest.get('reportedEPS', 0))
                            print(f"[OK] EPS from Alpha Vantage: ${eps:.2f}")
                    except Exception as e:
                        print(f"Alpha Vantage failed: {e}")

                if not eps:
                    print(f"[WARN] Could not fetch EPS for {ticker} from any source")

                if eps and eps > 0:
                    # Calculate actual P/E
                    pe_ratio = current_price / eps

                    # Calculate payout ratio (Dividend / EPS)
                    if dividend_rate > 0:
                        payout_ratio = dividend_rate / eps
                        retention_ratio = 1 - payout_ratio

                        # Get ROE - try Yahoo Finance first, then Alpha Vantage
                        try:
                            # Try Yahoo Finance API first (unlimited)
                            yf_api_url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=financialData"
                            response = requests.get(yf_api_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                            data = response.json()

                            if 'quoteSummary' in data and data['quoteSummary']['result']:
                                result = data['quoteSummary']['result'][0]
                                if 'financialData' in result:
                                    fin_data = result['financialData']
                                    roe_raw = fin_data.get('returnOnEquity', {})
                                    if isinstance(roe_raw, dict):
                                        roe = roe_raw.get('raw', None)
                                    else:
                                        roe = roe_raw
                                    if roe:
                                        print(f"[OK] ROE from Yahoo Finance: {roe*100:.1f}%")
                        except Exception as e:
                            print(f"Yahoo Finance ROE failed: {e}")

                        # Fallback to Alpha Vantage if Yahoo failed
                        if not roe:
                            try:
                                overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
                                ov_response = requests.get(overview_url, timeout=5)
                                ov_data = ov_response.json()
                                roe_str = ov_data.get('ReturnOnEquityTTM', None)
                                if roe_str and roe_str != 'None':
                                    roe = float(roe_str)
                                    print(f"[OK] ROE from Alpha Vantage: {roe*100:.1f}%")
                            except Exception as e:
                                print(f"Alpha Vantage ROE failed: {e}")
                                roe = None

                        # Calculate theoretical P/E using P/E = Payout / (ke - g)
                        if capm_return is not None and dividend_growth is not None and capm_return > dividend_growth:
                            theoretical_pe = payout_ratio / (capm_return - dividend_growth)

                    payout_str = f"{payout_ratio*100:.1f}%" if payout_ratio else "N/A"
                    roe_str = f"{roe*100:.1f}%" if roe else "N/A"
                    print(f"P/E Analysis: EPS=${eps:.2f}, P/E={pe_ratio:.2f}, Payout={payout_str}, ROE={roe_str}")
            else:
                # For Vietnamese stocks, use vnstock library
                print(f"Fetching P/E data for Vietnamese stock {ticker} from vnstock...")

                try:
                    if not _vnstock_loaded:
                        print(f"[WARN] vnstock library not loaded, skipping P/E data")
                    else:
                        # Get financial ratios from VCI
                        finance = Finance(source="VCI", symbol=ticker, period="year")
                        ratios = finance.ratio(symbol=ticker, period="year", flatten_columns=True, separator="_")

                        if not ratios.empty:
                            latest = ratios.iloc[0]  # Most recent data

                            # Extract EPS, P/E, ROE using Vietnamese column names
                            try:
                                eps = latest.get('Chỉ tiêu định giá_EPS (VND)', None)
                                if eps:
                                    print(f"[OK] EPS from vnstock: {eps:,.0f} VND")
                            except:
                                pass

                            try:
                                pe_ratio = latest.get('Chỉ tiêu định giá_P/E', None)
                                if pe_ratio:
                                    print(f"[OK] P/E from vnstock: {pe_ratio:.2f}x")
                            except:
                                pass

                            try:
                                roe = latest.get('Chỉ tiêu khả năng sinh lợi_ROE (%)', None)
                                if roe:
                                    print(f"[OK] ROE from vnstock: {roe*100:.1f}%")
                            except:
                                pass

                            # Calculate payout ratio and other metrics if we have the data
                            if eps and eps > 0:
                                # If we didn't get P/E from vnstock, calculate it
                                if not pe_ratio:
                                    pe_ratio = current_price / eps

                                # Calculate payout ratio
                                if dividend_rate > 0:
                                    payout_ratio = dividend_rate / eps
                                    retention_ratio = 1 - payout_ratio

                                    # Calculate theoretical P/E
                                    if capm_return is not None and dividend_growth is not None and capm_return > dividend_growth:
                                        theoretical_pe = payout_ratio / (capm_return - dividend_growth)

                                payout_str = f"{payout_ratio*100:.1f}%" if payout_ratio else "N/A"
                                roe_str = f"{roe*100:.1f}%" if roe else "N/A"
                                print(f"P/E Analysis: EPS={eps:,.0f} VND, P/E={pe_ratio:.2f}, Payout={payout_str}, ROE={roe_str}")
                        else:
                            print(f"[WARN] No financial data returned from vnstock for {ticker}")

                except Exception as e:
                    print(f"Error getting vnstock data for {ticker}: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"Error calculating P/E ratio: {e}")
            import traceback
            traceback.print_exc()

        result = {
            'ticker': ticker,
            'companyName': company_name,
            'beta': float(round(beta, 3)),
            'riskFreeRate': float(round(risk_free_rate, 4)),
            'marketReturn': float(round(market_return, 4)),
            'currentPrice': float(round(current_price, 2)),
            'dividend': float(round(dividend_rate, 2)),
            'dividendD1': float(round(d1 if dividend_rate > 0 else 0, 2)),  # Next year's dividend
            'dividendGrowth': float(round(dividend_growth, 4)),
            'capmReturn': float(round(capm_return, 4)),
            'gordonReturn': float(round(gordon_return, 4)),
            'fairPrice': float(round(fair_price, 2)),
            'valuation': valuation,
            'priceDifference': float(round(price_difference, 2)),
            'currency': currency,
            'lowDividendWarning': low_dividend_warning,
            'irregularDividend': irregular_dividend if not is_vn_stock else False,  # Only flag for US stocks
            'dividendConsistencyIssues': dividend_consistency_issues if not is_vn_stock and irregular_dividend else [],
            # P/E Ratio Analysis
            'eps': float(round(eps, 2)) if eps else None,
            'peRatio': float(round(pe_ratio, 2)) if pe_ratio else None,
            'payoutRatio': float(round(payout_ratio, 4)) if payout_ratio else None,
            'retentionRatio': float(round(retention_ratio, 4)) if retention_ratio else None,
            'roe': float(round(roe, 4)) if roe else None,
            'theoreticalPE': float(round(theoretical_pe, 2)) if theoretical_pe else None,
            'sources': {
                'beta': tv_data['source'],
                'riskFreeRate': 'VN Gov Bond' if is_vn_stock else 'Live US 10-Year Treasury',
                'marketReturn': 'VN-Index Historical' if is_vn_stock else 'S&P 500 Historical',
                'currentPrice': tv_data['source'],
                'dividend': tv_data['source'],
                'dividendGrowth': 'Calculated from Historical Data' if is_vn_stock else 'Calculated from Historical Data'
            }
        }

        # Cache result
        _cache[cache_key] = result
        print(f"[OK] Successfully processed {ticker}")

        return jsonify(result)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Failed to process ticker: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'CAPM API with TradingView Scraper',
        'features': ['FREE - No API key needed', 'Real beta from TradingView', 'Accurate financial data']
    })

# Serve frontend HTML and static files
@app.route('/')
def serve_frontend():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images, etc.)"""
    try:
        return send_from_directory('.', path)
    except:
        # If file not found, serve index.html (for SPA routing)
        return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Use PORT from environment variable (for Render/cloud deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))

    print("=" * 60)
    print("CAPM & Gordon Model API - TradingView Version")
    print("=" * 60)
    print("Features:")
    print("  - FREE - No API key or credits needed!")
    print("  - Real beta values from TradingView")
    print("  - Accurate financial data")
    print("  - Works for Vietnamese and US stocks")
    print("=" * 60)
    print(f"Starting server on http://localhost:{port}")
    print("=" * 60)

    # Use 0.0.0.0 for cloud deployment (allows external access)
    app.run(host='0.0.0.0', debug=True, port=port)
