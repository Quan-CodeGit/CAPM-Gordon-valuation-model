"""
Backend using Damodaran Method for CAPM calculation
Uses Country Risk Premium approach from Professor Aswath Damodaran (NYU Stern)
Data updated: January 5, 2026

Key differences from standard backend:
1. Uses US 10Y Treasury as global risk-free rate
2. Adds Country Risk Premium based on sovereign ratings
3. Uses Mature Market ERP (4.23%) + Country Risk Premium
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
finally:
    sys.stderr = _original_stderr
    sys.stdout = _original_stdout

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import json
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
CORS(app)

# ============================================================================
# DAMODARAN METHODOLOGY - January 2026 Update
# Source: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html
# ============================================================================

# Damodaran Country Risk Premiums (January 5, 2026)
# Format: Country -> (Moody's Rating, Adj. Default Spread, Country Risk Premium, Total Equity Risk Premium)
DAMODARAN_COUNTRY_DATA = {
    'US': {
        'rating': 'Aa1',
        'default_spread': 0.0023,      # 0.23%
        'country_risk_premium': 0.0023, # 0.23%
        'total_erp': 0.0446,           # 4.46%
    },
    'AU': {
        'rating': 'Aaa',
        'default_spread': 0.0000,      # 0.00%
        'country_risk_premium': 0.0000, # 0.00%
        'total_erp': 0.0423,           # 4.23% (Mature Market ERP)
    },
    'VN': {
        'rating': 'Ba2',
        'default_spread': 0.0256,      # 2.56%
        'country_risk_premium': 0.0390, # 3.90%
        'total_erp': 0.0813,           # 8.13%
    },
}

# Mature Market Equity Risk Premium (Base ERP for Aaa-rated countries)
MATURE_MARKET_ERP = 0.0423  # 4.23%

def get_damodaran_erp(market):
    """
    Get Damodaran's Total Equity Risk Premium for a market

    Damodaran Method:
    Total ERP = Mature Market ERP + Country Risk Premium

    For CAPM:
    Required Return = Risk-Free Rate + Beta × Total ERP
    """
    if market in DAMODARAN_COUNTRY_DATA:
        data = DAMODARAN_COUNTRY_DATA[market]
        return data['total_erp'], data['country_risk_premium'], data['rating']
    else:
        # Default to US if unknown market
        return DAMODARAN_COUNTRY_DATA['US']['total_erp'], 0.0023, 'Aa1'

# ============================================================================
# End of Damodaran-specific constants
# ============================================================================

# Alpha Vantage API Key for P/E data
ALPHA_VANTAGE_API_KEY = "PN4MBNMUOULYYXVC"

# Cache results
_cache = {}
_cache_timeout = 300  # 5 minutes

# Dividend growth cache file
DIVIDEND_GROWTH_CACHE_FILE = 'dividend_growth_cache.json'
CACHE_EXPIRY_DAYS = 30

def load_dividend_growth_cache():
    """Load cached dividend growth rates from JSON file"""
    try:
        if os.path.exists(DIVIDEND_GROWTH_CACHE_FILE):
            with open(DIVIDEND_GROWTH_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading dividend growth cache: {e}")
    return {}

def save_dividend_growth_cache(cache):
    """Save dividend growth rates to JSON file"""
    try:
        with open(DIVIDEND_GROWTH_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Error saving dividend growth cache: {e}")

def is_cache_expired(timestamp_str, days=CACHE_EXPIRY_DAYS):
    """Check if cached data is older than specified days"""
    try:
        cached_date = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - cached_date
        return age.days > days
    except:
        return True

# Vietnamese stocks list
VIETNAMESE_STOCKS = [
    'VIC', 'VHM', 'TCB', 'FPT', 'VPB', 'LPB', 'HPG', 'HDB', 'ACB', 'MBB',
    'MWG', 'STB', 'MSN', 'VCB', 'VJC', 'SHB', 'SSI', 'VNM', 'CTG', 'VIB',
    'VRE', 'SSB', 'TPB', 'DGC', 'BID', 'GAS', 'SAB', 'PLX', 'GVR', 'BCM',
    'EIB', 'KBC', 'OCB', 'LPB', 'TPB', 'SHB', 'STB', 'VIB', 'NAB', 'VAB',
    'NVL', 'KDH', 'DXG', 'PDR', 'DIG', 'HDC', 'CEO', 'NLG', 'BCG', 'CTD',
    'HBC', 'LDG', 'PDR', 'QCG', 'SCR', 'SZC',
    'VHC', 'MCH', 'VNL', 'BBC', 'SBT', 'KDC',
    'VGI', 'CMG', 'ITD', 'CTR', 'ELC', 'FOX',
    'HSG', 'NKG', 'DCM', 'DPM', 'NT2', 'HT1', 'VCS', 'VGC', 'VSC', 'VHC',
    'POW', 'PVD', 'PVT', 'BSR', 'PVS', 'PVG', 'POW', 'GEG', 'PPC', 'NT2',
    'PNJ', 'FRT', 'DGW', 'PET', 'TCM',
    'VCI', 'VND', 'HCM', 'MBS', 'VIX', 'AGR', 'BSI', 'CTS', 'FTS',
    'BVH', 'BMI', 'BIC', 'PRE', 'PVI', 'MIG',
    'HVN', 'VTP', 'GMD', 'HAH', 'VJC', 'ACV', 'VOS',
    'TNG', 'MSH', 'GIL', 'TCL', 'VGT', 'STK',
    'HNG', 'HAG', 'LSS', 'SBT', 'BAF',
    'GEX', 'DHG', 'REE', 'DPR', 'PC1', 'VPI', 'IDC', 'PAN', 'PHR', 'SCS',
    'TRA', 'VCS', 'VGI', 'VHM', 'VIC', 'VND', 'VNM', 'VSH'
]

# Fallback dividend data for major Vietnamese stocks
DIVIDEND_FALLBACK = {
    'VNM': {'dividend': 3000, 'growth': 0.04},
    'VCB': {'dividend': 1500, 'growth': 0.08},
    'FPT': {'dividend': 2500, 'growth': 0.12},
    'HPG': {'dividend': 1800, 'growth': 0.06},
    'TCB': {'dividend': 1000, 'growth': 0.10},
    'SAB': {'dividend': 2200, 'growth': 0.04},
    'GAS': {'dividend': 4000, 'growth': 0.04},
    'MBB': {'dividend': 800, 'growth': 0.09},
    'VHM': {'dividend': 2000, 'growth': 0.03},
    'MSN': {'dividend': 1200, 'growth': 0.05},
    'VIC': {'dividend': 1500, 'growth': 0.05},
    'PLX': {'dividend': 2000, 'growth': 0.04},
    'BVH': {'dividend': 1800, 'growth': 0.05},
    'KBC': {'dividend': 500, 'growth': 0.07},
    'PVS': {'dividend': 800, 'growth': 0.04},
}

# Dividend growth rates for major AU/US stocks
DIVIDEND_GROWTH_DATABASE = {
    'CBA': 0.09, 'CSL': 0.09, 'ANZ': 0.08, 'WBC': 0.07, 'NAB': 0.07,
    'BHP': 0.08, 'WES': 0.06, 'WOW': 0.05, 'TLS': 0.03, 'RIO': 0.12,
    'KO': 0.03, 'PEP': 0.07, 'JNJ': 0.06, 'PG': 0.05, 'WMT': 0.02,
    'MCD': 0.08, 'MSFT': 0.10, 'AAPL': 0.08, 'V': 0.17, 'MA': 0.16,
}

def get_vn_dividend_data(ticker):
    """Get Vietnamese stock dividend data"""
    try:
        from vnstock import Vnstock
        print(f"Fetching Vietnamese dividend data for {ticker} from vnstock...")
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        ratios = stock.finance.ratio(period='year', lang='en')

        if ratios is not None and not ratios.empty:
            if 'dividendPerShare' in ratios.columns:
                dividends = ratios['dividendPerShare'].head(2)
                if len(dividends) >= 1 and not pd.isna(dividends.iloc[0]) and dividends.iloc[0] > 0:
                    latest_div = float(dividends.iloc[0]) * 1000
                    if len(dividends) >= 2 and not pd.isna(dividends.iloc[1]) and dividends.iloc[1] > 0:
                        prev_div = float(dividends.iloc[1]) * 1000
                        growth = (latest_div / prev_div) - 1
                        return latest_div, growth
                    else:
                        fallback_growth = DIVIDEND_FALLBACK.get(ticker, {}).get('growth', 0.05)
                        return latest_div, fallback_growth
    except Exception as e:
        print(f"Error fetching vnstock dividend data: {e}")

    if ticker in DIVIDEND_FALLBACK:
        fallback = DIVIDEND_FALLBACK[ticker]
        return fallback['dividend'], fallback['growth']

    return 0, 0.05

def get_dividend_growth_from_history(ticker, is_au_stock=False, max_retries=2):
    """Calculate historical dividend growth with caching"""
    cache = load_dividend_growth_cache()

    if ticker in cache:
        cache_entry = cache[ticker]
        if not is_cache_expired(cache_entry.get('timestamp', '')):
            growth = cache_entry.get('growth', 0.03)
            return growth, growth, False, None

    if ticker in DIVIDEND_GROWTH_DATABASE:
        growth = DIVIDEND_GROWTH_DATABASE[ticker]
        cache[ticker] = {
            'growth': growth,
            'timestamp': datetime.now().isoformat(),
            'source': 'manual_database'
        }
        save_dividend_growth_cache(cache)
        return growth, growth, False, None

    try:
        import yfinance as yf
        yf_ticker = ticker + ".AX" if is_au_stock else ticker

        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(yf_ticker)
                dividends = stock.dividends
                if len(dividends) > 0:
                    break
                time.sleep(2)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)

        if dividends is None or len(dividends) < 2:
            return 0.03, None, False, None

        annual_divs = dividends.resample('Y').sum()
        if len(annual_divs) < 2:
            return 0.03, None, False, None

        years = len(annual_divs) - 1
        latest = annual_divs.iloc[-1]
        oldest = annual_divs.iloc[0]

        if oldest <= 0:
            previous = annual_divs.iloc[-2]
            if previous > 0:
                yoy_growth = (latest / previous) - 1
                return yoy_growth, yoy_growth, False, None
            return 0.03, None, False, None

        cagr = (latest / oldest) ** (1 / years) - 1

        cache[ticker] = {
            'growth': cagr,
            'timestamp': datetime.now().isoformat(),
            'source': 'yfinance',
            'years': years
        }
        save_dividend_growth_cache(cache)

        return cagr, cagr, False, None
    except Exception as e:
        return 0.03, None, False, None

def get_tradingview_data(ticker, is_vn_stock=False, is_au_stock=False):
    """Fetch stock data from TradingView"""
    try:
        from tradingview_scraper.symbols.overview import Overview

        if is_vn_stock:
            exchanges = ['HOSE', 'HNX']
        elif is_au_stock:
            exchanges = ['ASX']
        else:
            exchanges = ['NASDAQ', 'NYSE', 'AMEX']

        overview = Overview()
        data = None

        for exchange in exchanges:
            try:
                tv_symbol = f"{exchange}:{ticker}"
                result = overview.get_symbol_overview(symbol=tv_symbol)
                if result and 'data' in result:
                    data = result['data']
                    break
            except:
                continue

        if not data:
            return None

        current_price = data.get('close', 0)
        beta = data.get('beta_1_year', 1.0)
        company_name = data.get('description', ticker)
        dividend_yield_percent = data.get('dividends_yield', 0)
        div_per_share_fy = data.get('dividends_per_share_fy', None)
        pe_ratio_tv = data.get('price_earnings_ttm', None)
        eps_tv = data.get('earnings_per_share_diluted_ttm', None)

        dividend_yield = dividend_yield_percent / 100 if dividend_yield_percent else 0

        if div_per_share_fy and div_per_share_fy > 0:
            dividend_rate = div_per_share_fy
        else:
            dividend_rate = current_price * dividend_yield if dividend_yield else 0

        return {
            'currentPrice': current_price,
            'beta': beta if beta is not None else 1.0,
            'companyName': company_name,
            'dividend': dividend_rate,
            'dividendYield': dividend_yield,
            'peRatio': pe_ratio_tv,
            'eps': eps_tv,
            'source': f'TradingView ({exchange}:{ticker})'
        }
    except ImportError:
        return None
    except Exception as e:
        return None

def get_us_risk_free_rate():
    """Get live US 10-year Treasury yield (used as global risk-free rate in Damodaran method)"""
    try:
        import yfinance as yf
        treasury = yf.Ticker("^TNX")
        treasury_data = treasury.history(period="5d")
        if not treasury_data.empty:
            rate = treasury_data['Close'].iloc[-1] / 100
            print(f"[DAMODARAN] Live US 10Y Treasury rate: {rate*100:.2f}%")
            return rate
    except:
        pass
    print(f"[DAMODARAN] Using fallback US 10Y Treasury rate: 4.20%")
    return 0.042

@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()
        market = request.args.get('market', 'VN').upper()

        print(f"\n{'='*60}")
        print(f"[DAMODARAN METHOD] Processing {ticker} (Market: {market})")
        print(f"{'='*60}")

        # Check cache
        cache_key = f"damodaran_{ticker}_{market}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        time.sleep(1)

        # Determine market type
        if market == 'VN':
            is_vn_stock = True
            is_au_stock = False
        elif market == 'AU':
            is_vn_stock = False
            is_au_stock = True
        else:
            is_vn_stock = False
            is_au_stock = False

        # Get TradingView data
        tv_data = get_tradingview_data(ticker, is_vn_stock, is_au_stock)
        if not tv_data:
            return jsonify({'error': f'Unable to fetch data for {ticker} from TradingView'}), 400

        current_price = tv_data['currentPrice']
        beta = tv_data['beta']
        company_name = tv_data['companyName']
        dividend_rate = tv_data['dividend']

        # ============================================================
        # DAMODARAN METHOD - Key difference from standard backend
        # ============================================================

        # Step 1: Get US Risk-Free Rate (used globally)
        risk_free_rate = get_us_risk_free_rate()

        # Step 2: Get Country-Specific Equity Risk Premium from Damodaran data
        total_erp, country_risk_premium, sovereign_rating = get_damodaran_erp(market)

        print(f"[DAMODARAN] Country: {market}")
        print(f"[DAMODARAN] Sovereign Rating: {sovereign_rating}")
        print(f"[DAMODARAN] Country Risk Premium: {country_risk_premium*100:.2f}%")
        print(f"[DAMODARAN] Total Equity Risk Premium: {total_erp*100:.2f}%")
        print(f"[DAMODARAN] Risk-Free Rate (US 10Y): {risk_free_rate*100:.2f}%")

        # Step 3: Calculate CAPM using Damodaran method
        # Required Return = Risk-Free Rate + Beta × Total ERP
        capm_return = risk_free_rate + beta * total_erp

        print(f"[DAMODARAN] CAPM = {risk_free_rate*100:.2f}% + {beta:.2f} × {total_erp*100:.2f}% = {capm_return*100:.2f}%")

        # ============================================================
        # End of Damodaran-specific calculation
        # ============================================================

        # Set currency based on market
        if is_vn_stock:
            currency = 'VND'
        elif is_au_stock:
            currency = 'AUD'
        else:
            currency = 'USD'

        # Initialize variables
        historical_growth = None
        dividend_growth = 0.05
        irregular_dividend = False
        dividend_consistency_issues = []
        yf_stock = None

        # Get dividend data based on market
        if is_vn_stock:
            if ticker in DIVIDEND_FALLBACK:
                fallback = DIVIDEND_FALLBACK[ticker]
                dividend_rate = fallback['dividend']
                dividend_growth = fallback['growth']
            else:
                vn_dividend, vn_growth = get_vn_dividend_data(ticker)
                dividend_rate = vn_dividend
                dividend_growth = vn_growth
        else:
            dividend_growth, historical_growth, _, _ = get_dividend_growth_from_history(ticker, is_au_stock)
            try:
                import yfinance as yf
                yf_ticker = ticker + ".AX" if is_au_stock else ticker
                yf_stock = yf.Ticker(yf_ticker)
            except:
                pass

        # Apply growth capping
        growth_warning = None
        historical_dividend_growth = historical_growth

        if dividend_growth >= capm_return - 0.02:
            historical_dividend_growth = dividend_growth
            conservative_cap = 0.05
            dynamic_cap = max(capm_return - 0.03, 0.03)
            dividend_growth = min(conservative_cap, dynamic_cap)
            growth_warning = f"Historical dividend growth ({historical_dividend_growth*100:.1f}%) exceeds sustainable level. Using capped rate ({dividend_growth*100:.1f}%) for valuation."

        # Calculate Gordon Model
        if dividend_rate > 0:
            d1 = dividend_rate * (1 + dividend_growth)
            dividend_yield_d1 = d1 / current_price
            gordon_return = dividend_yield_d1 + dividend_growth

            if capm_return > dividend_growth:
                fair_price = d1 / (capm_return - dividend_growth)
            else:
                fair_price = current_price
        else:
            d1 = 0
            gordon_return = dividend_growth
            fair_price = current_price

        # Determine valuation
        valuation = "OVERVALUED" if gordon_return < capm_return else "UNDERVALUED"
        price_difference = ((fair_price - current_price) / current_price) * 100

        # Check for low dividend
        dividend_yield = (dividend_rate / current_price) if dividend_rate > 0 else 0
        low_dividend_warning = None
        if dividend_yield < 0.01 and dividend_rate > 0:
            low_dividend_warning = "Low dividend yield - Gordon Model may not be appropriate."
        elif dividend_rate == 0:
            low_dividend_warning = "No dividend - Gordon Model does not apply."

        # P/E calculation (simplified for this version)
        eps = tv_data.get('eps')
        pe_ratio = tv_data.get('peRatio')
        payout_ratio = None
        retention_ratio = None
        roe = None
        theoretical_pe = None

        if eps and eps > 0:
            if not pe_ratio:
                pe_ratio = current_price / eps
            if dividend_rate > 0:
                payout_ratio = dividend_rate / eps
                retention_ratio = 1 - payout_ratio
                if capm_return > dividend_growth:
                    theoretical_pe = payout_ratio / (capm_return - dividend_growth)

        result = {
            'ticker': ticker,
            'companyName': company_name,
            'beta': float(round(beta, 3)),
            'riskFreeRate': float(round(risk_free_rate, 4)),
            'marketReturn': None,  # Not used in Damodaran method
            'totalErp': float(round(total_erp, 4)),
            'countryRiskPremium': float(round(country_risk_premium, 4)),
            'sovereignRating': sovereign_rating,
            'currentPrice': float(round(current_price, 2)),
            'dividend': float(round(dividend_rate, 2)),
            'dividendD1': float(round(d1 if dividend_rate > 0 else 0, 2)),
            'dividendGrowth': float(round(dividend_growth, 4)),
            'historicalDividendGrowth': float(round(historical_dividend_growth, 4)) if historical_dividend_growth else None,
            'growthWarning': growth_warning,
            'capmReturn': float(round(capm_return, 4)),
            'gordonReturn': float(round(gordon_return, 4)),
            'fairPrice': float(round(fair_price, 2)),
            'valuation': valuation,
            'priceDifference': float(round(price_difference, 2)),
            'currency': currency,
            'lowDividendWarning': low_dividend_warning,
            'irregularDividend': False,
            'dividendConsistencyIssues': [],
            'eps': float(round(eps, 2)) if eps else None,
            'peRatio': float(round(pe_ratio, 2)) if pe_ratio else None,
            'payoutRatio': float(round(payout_ratio, 4)) if payout_ratio else None,
            'retentionRatio': float(round(retention_ratio, 4)) if retention_ratio else None,
            'roe': float(round(roe, 4)) if roe else None,
            'theoreticalPE': float(round(theoretical_pe, 2)) if theoretical_pe else None,
            'methodology': 'Damodaran',
            'methodologyNote': f'Using Damodaran Country Risk Premium method. Total ERP ({total_erp*100:.2f}%) = Mature Market ERP ({MATURE_MARKET_ERP*100:.2f}%) + Country Risk Premium ({country_risk_premium*100:.2f}%)',
            'sources': {
                'beta': tv_data['source'],
                'riskFreeRate': 'US 10-Year Treasury (Damodaran method uses US rate globally)',
                'equityRiskPremium': f'Damodaran Country Risk Data (Jan 2026) - {sovereign_rating} rated',
                'currentPrice': tv_data['source'],
                'dividend': tv_data['source'],
                'dividendGrowth': 'Calculated from Historical Data'
            }
        }

        _cache[cache_key] = result
        print(f"[DAMODARAN] Successfully processed {ticker}")

        return jsonify(result)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process ticker: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'CAPM API - Damodaran Method',
        'methodology': 'Damodaran Country Risk Premium',
        'dataSource': 'NYU Stern - January 2026',
        'features': [
            'Uses US 10Y Treasury as global risk-free rate',
            'Adds Country Risk Premium based on sovereign ratings',
            'Vietnam: Ba2 rating, 3.90% country risk premium',
            'Australia: Aaa rating, 0% country risk premium',
            'US: Aa1 rating, 0.23% country risk premium'
        ]
    })

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index_damodaran.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('.', path)
    except:
        return send_from_directory('.', 'index_damodaran.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Use port 5001 to avoid conflict

    print("=" * 60)
    print("CAPM & Gordon Model API - DAMODARAN METHOD")
    print("=" * 60)
    print("Methodology: Damodaran Country Risk Premium")
    print("Data Source: NYU Stern (January 5, 2026)")
    print("")
    print("Country Risk Premiums:")
    print(f"  Vietnam (Ba2):   {DAMODARAN_COUNTRY_DATA['VN']['total_erp']*100:.2f}% Total ERP")
    print(f"  Australia (Aaa): {DAMODARAN_COUNTRY_DATA['AU']['total_erp']*100:.2f}% Total ERP")
    print(f"  US (Aa1):        {DAMODARAN_COUNTRY_DATA['US']['total_erp']*100:.2f}% Total ERP")
    print("=" * 60)
    print(f"Starting server on http://localhost:{port}")
    print("=" * 60)

    app.run(host='0.0.0.0', debug=True, port=port)
