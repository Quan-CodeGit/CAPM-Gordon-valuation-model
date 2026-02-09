"""
Backend for Render.com deployment
Uses TradingView Scraper + yfinance (no vnstock - not needed for cloud)
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import json
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)

# Cache results
_cache = {}
_cache_timeout = 300  # 5 minutes

# Dividend growth cache file
DIVIDEND_GROWTH_CACHE_FILE = 'dividend_growth_cache.json'
CACHE_EXPIRY_DAYS = 30

def load_dividend_growth_cache():
    try:
        if os.path.exists(DIVIDEND_GROWTH_CACHE_FILE):
            with open(DIVIDEND_GROWTH_CACHE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_dividend_growth_cache(cache):
    try:
        with open(DIVIDEND_GROWTH_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass

def is_cache_expired(timestamp_str, days=CACHE_EXPIRY_DAYS):
    try:
        cached_date = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - cached_date
        return age.days > days
    except:
        return True

# Vietnamese stocks fallback data
DIVIDEND_FALLBACK_VN = {
    'VNM': {'dividend': 3000, 'growth': 0.04, 'beta': 0.85, 'price': 72000, 'name': 'Vinamilk'},
    'VCB': {'dividend': 1500, 'growth': 0.08, 'beta': 1.15, 'price': 95000, 'name': 'Vietcombank'},
    'FPT': {'dividend': 2500, 'growth': 0.12, 'beta': 1.20, 'price': 135000, 'name': 'FPT Corporation'},
    'HPG': {'dividend': 1800, 'growth': 0.06, 'beta': 1.45, 'price': 26000, 'name': 'Hoa Phat Group'},
    'TCB': {'dividend': 1000, 'growth': 0.10, 'beta': 1.30, 'price': 25000, 'name': 'Techcombank'},
    'SAB': {'dividend': 2200, 'growth': 0.04, 'beta': 0.75, 'price': 58000, 'name': 'Sabeco'},
    'GAS': {'dividend': 4000, 'growth': 0.04, 'beta': 0.90, 'price': 75000, 'name': 'PV Gas'},
    'MBB': {'dividend': 800, 'growth': 0.09, 'beta': 1.25, 'price': 22000, 'name': 'Military Bank'},
    'VHM': {'dividend': 2000, 'growth': 0.03, 'beta': 1.35, 'price': 42000, 'name': 'Vinhomes'},
    'MSN': {'dividend': 1200, 'growth': 0.05, 'beta': 1.10, 'price': 85000, 'name': 'Masan Group'},
    'VIC': {'dividend': 1500, 'growth': 0.05, 'beta': 1.40, 'price': 43000, 'name': 'Vingroup'},
    'PLX': {'dividend': 2000, 'growth': 0.04, 'beta': 0.95, 'price': 42000, 'name': 'Petrolimex'},
    'BVH': {'dividend': 1800, 'growth': 0.05, 'beta': 1.00, 'price': 48000, 'name': 'Bao Viet'},
    'ACB': {'dividend': 700, 'growth': 0.08, 'beta': 1.20, 'price': 25000, 'name': 'ACB Bank'},
    'BID': {'dividend': 1000, 'growth': 0.07, 'beta': 1.15, 'price': 48000, 'name': 'BIDV'},
    'CTG': {'dividend': 800, 'growth': 0.06, 'beta': 1.18, 'price': 35000, 'name': 'VietinBank'},
    'VPB': {'dividend': 500, 'growth': 0.09, 'beta': 1.35, 'price': 20000, 'name': 'VPBank'},
    'HDB': {'dividend': 600, 'growth': 0.10, 'beta': 1.28, 'price': 24000, 'name': 'HDBank'},
    'STB': {'dividend': 400, 'growth': 0.07, 'beta': 1.22, 'price': 32000, 'name': 'Sacombank'},
    'SSI': {'dividend': 1000, 'growth': 0.08, 'beta': 1.40, 'price': 32000, 'name': 'SSI Securities'},
    'MWG': {'dividend': 1500, 'growth': 0.06, 'beta': 1.25, 'price': 55000, 'name': 'Mobile World'},
    'PNJ': {'dividend': 2000, 'growth': 0.10, 'beta': 1.15, 'price': 85000, 'name': 'PNJ'},
    'REE': {'dividend': 1500, 'growth': 0.05, 'beta': 1.05, 'price': 68000, 'name': 'REE Corp'},
    'DGC': {'dividend': 3000, 'growth': 0.08, 'beta': 1.30, 'price': 85000, 'name': 'DGC'},
    'ACV': {'dividend': 2500, 'growth': 0.06, 'beta': 0.95, 'price': 85000, 'name': 'Airports Corp'},
}

# Dividend growth database for AU/US stocks
DIVIDEND_GROWTH_DATABASE = {
    'CBA': 0.09, 'CSL': 0.09, 'ANZ': 0.08, 'WBC': 0.07, 'NAB': 0.07,
    'BHP': 0.08, 'WES': 0.06, 'WOW': 0.05, 'TLS': 0.03, 'RIO': 0.12,
    'KO': 0.03, 'PEP': 0.07, 'JNJ': 0.06, 'PG': 0.05, 'WMT': 0.02,
    'MCD': 0.08, 'MSFT': 0.10, 'AAPL': 0.08, 'V': 0.17, 'MA': 0.16,
}

def get_usd_vnd_rate():
    """Get USD/VND exchange rate from TradingView (cached)"""
    global _cache
    cache_key = f"USDVND_{int(time.time() / 3600)}"  # Cache for 1 hour
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        from tradingview_scraper.symbols.overview import Overview
        overview = Overview()
        result = overview.get_symbol_overview(symbol='FX_IDC:USDVND')
        if result and 'data' in result:
            rate = result['data'].get('close', 25500)
            _cache[cache_key] = rate
            print(f"[FX] USD/VND rate: {rate}")
            return rate
    except:
        pass
    return 25500  # Fallback rate

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

        # Debug: Print all available fields for VN stocks
        if is_vn_stock:
            eps_fields = {k: data.get(k) for k in data.keys() if 'eps' in k.lower() or 'earning' in k.lower()}
            pe_fields = {k: data.get(k) for k in data.keys() if 'p/e' in k.lower() or 'pe' in k.lower() or 'price_earning' in k.lower()}
            print(f"[DEBUG TV] {ticker} EPS-related fields: {eps_fields}")
            print(f"[DEBUG TV] {ticker} P/E-related fields: {pe_fields}")

        current_price = data.get('close', 0)
        beta = data.get('beta_1_year', 1.0)
        company_name = data.get('description', ticker)
        dividend_yield_percent = data.get('dividends_yield', 0)
        div_per_share_fy = data.get('dividends_per_share_fy', None)
        pe_ratio = data.get('price_earnings_ttm', None)

        # Get EPS from TradingView
        # IMPORTANT: For VN stocks, TradingView API returns EPS in USD (not VND)
        # e.g., VCB EPS = 0.16 USD = ~4,210 VND. Must convert using exchange rate.
        eps_diluted_ttm = data.get('earnings_per_share_diluted_ttm', None)
        eps_basic_ttm = data.get('earnings_per_share_basic_ttm', None)
        eps_fq = data.get('earnings_per_share_fq', None)

        if is_vn_stock:
            # For VN stocks, pick the best TTM EPS (in USD), prefer basic over diluted
            # TradingView sometimes returns None for diluted on VN stocks
            candidates = [v for v in [eps_diluted_ttm, eps_basic_ttm] if v and v > 0]
            eps = max(candidates) if candidates else None
            print(f"[DEBUG TV] {ticker} EPS (USD): diluted_ttm={eps_diluted_ttm}, basic_ttm={eps_basic_ttm} → chosen={eps}")
        else:
            eps = eps_diluted_ttm
            if not eps:
                eps = eps_basic_ttm
            if not eps:
                eps = eps_fq

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
            'peRatio': pe_ratio,
            'eps': eps,
            'source': f'TradingView ({exchange}:{ticker})'
        }
    except Exception as e:
        print(f"TradingView error for {ticker}: {e}")
        return None

def get_dividend_growth(ticker, is_au_stock=False):
    """Get dividend growth rate"""
    cache = load_dividend_growth_cache()

    if ticker in cache and not is_cache_expired(cache[ticker].get('timestamp', '')):
        return cache[ticker].get('growth', 0.03)

    if ticker in DIVIDEND_GROWTH_DATABASE:
        return DIVIDEND_GROWTH_DATABASE[ticker]

    try:
        import yfinance as yf
        yf_ticker = ticker + ".AX" if is_au_stock else ticker
        stock = yf.Ticker(yf_ticker)
        dividends = stock.dividends

        if dividends is None or len(dividends) < 2:
            return 0.03

        annual_divs = dividends.resample('YE').sum()
        if len(annual_divs) < 2:
            return 0.03

        years = len(annual_divs) - 1
        latest = annual_divs.iloc[-1]
        oldest = annual_divs.iloc[0]

        if oldest <= 0:
            return 0.03

        cagr = (latest / oldest) ** (1 / years) - 1
        cagr = max(min(cagr, 0.20), -0.10)

        cache[ticker] = {'growth': cagr, 'timestamp': datetime.now().isoformat()}
        save_dividend_growth_cache(cache)

        return cagr
    except:
        return 0.03

def get_risk_free_rate():
    """Get US 10Y Treasury rate"""
    try:
        import yfinance as yf
        treasury = yf.Ticker("^TNX")
        data = treasury.history(period="5d")
        if not data.empty:
            return data['Close'].iloc[-1] / 100
    except:
        pass
    return 0.042

@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()
        market = request.args.get('market', 'US').upper()

        print(f"\n{'='*50}")
        print(f"Processing {ticker} (Market: {market})")
        print(f"{'='*50}")

        cache_key = f"{ticker}_{market}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        is_vn_stock = market == 'VN'
        is_au_stock = market == 'AU'

        # Vietnamese stocks - try TradingView first, fallback if fails
        if is_vn_stock:
            tv_data = get_tradingview_data(ticker, is_vn_stock=True)

            if tv_data and tv_data['currentPrice'] > 0:
                # Use TradingView data
                current_price = tv_data['currentPrice']
                beta = tv_data['beta']
                company_name = tv_data['companyName']
                source = tv_data['source']

                # For VN stocks, dividend is calculated from yield × close price (both in VND)
                # div_per_share_fy is always None for VN stocks, so yield-based calc is used
                # No conversion needed since close is already in VND
                dividend_rate = tv_data['dividend']

                # Get EPS in VND from TradingView
                # Method 1 (preferred): If TradingView provides P/E, derive EPS = Price / P/E
                #   This gives exact VND values matching TradingView's website
                # Method 2 (fallback): Convert EPS from USD to VND using exchange rate
                #   TradingView API returns VN EPS in USD, so slight rounding difference
                tv_pe = tv_data['peRatio']
                raw_eps = tv_data['eps']  # EPS in USD

                if tv_pe and tv_pe > 0 and current_price > 0:
                    # Best: derive EPS directly from P/E (exact match with TradingView website)
                    eps = current_price / tv_pe
                    pe_ratio = tv_pe
                    print(f"[DEBUG] {ticker} EPS from P/E: {current_price} / {tv_pe:.2f} = {eps:.0f} VND")
                elif raw_eps and raw_eps > 0:
                    # Fallback: convert EPS from USD to VND
                    usd_vnd_rate = get_usd_vnd_rate()
                    eps = raw_eps * usd_vnd_rate
                    pe_ratio = current_price / eps if eps > 0 else None
                    print(f"[DEBUG] {ticker} EPS from USD: {raw_eps:.4f} × {usd_vnd_rate} = {eps:.0f} VND" + (f", P/E = {pe_ratio:.2f}" if pe_ratio else ""))
                else:
                    eps = None
                    pe_ratio = None
                    print(f"[DEBUG] {ticker} No EPS data available")

                # Get dividend growth from fallback if available, else default
                if ticker in DIVIDEND_FALLBACK_VN:
                    dividend_growth = DIVIDEND_FALLBACK_VN[ticker]['growth']
                else:
                    dividend_growth = 0.05
            elif ticker in DIVIDEND_FALLBACK_VN:
                # Fallback to database if TradingView fails
                fallback = DIVIDEND_FALLBACK_VN[ticker]
                current_price = fallback['price']
                beta = fallback['beta']
                dividend_rate = fallback['dividend']
                dividend_growth = fallback['growth']
                company_name = fallback['name']
                eps = None
                pe_ratio = None
                source = 'Fallback Database (TradingView unavailable)'
            else:
                return jsonify({'error': f'Stock {ticker} not found on TradingView or in database'}), 400

            risk_free_rate = 0.0416
            market_return = 0.09
            currency = 'VND'
        else:
            # US/AU stocks - use TradingView
            tv_data = get_tradingview_data(ticker, is_vn_stock=False, is_au_stock=is_au_stock)

            if not tv_data:
                return jsonify({'error': f'Unable to fetch data for {ticker}'}), 400

            current_price = tv_data['currentPrice']
            beta = tv_data['beta']
            company_name = tv_data['companyName']
            dividend_rate = tv_data['dividend']
            eps = tv_data['eps']
            pe_ratio = tv_data['peRatio']
            source = tv_data['source']

            dividend_growth = get_dividend_growth(ticker, is_au_stock)
            risk_free_rate = get_risk_free_rate()

            if is_au_stock:
                market_return = 0.095
                currency = 'AUD'
            else:
                market_return = 0.10
                currency = 'USD'

        # Calculate CAPM
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)

        # Cap dividend growth if needed
        growth_warning = None
        historical_growth = dividend_growth
        if dividend_growth >= capm_return - 0.02:
            historical_growth = dividend_growth
            dividend_growth = min(0.05, max(capm_return - 0.03, 0.03))
            growth_warning = f"Growth capped from {historical_growth*100:.1f}% to {dividend_growth*100:.1f}%"

        # Gordon Model
        if dividend_rate > 0:
            d1 = dividend_rate * (1 + dividend_growth)
            gordon_return = (d1 / current_price) + dividend_growth
            if capm_return > dividend_growth:
                fair_price = d1 / (capm_return - dividend_growth)
            else:
                fair_price = current_price
        else:
            d1 = 0
            gordon_return = dividend_growth
            fair_price = current_price

        valuation = "OVERVALUED" if gordon_return < capm_return else "UNDERVALUED"
        price_difference = ((fair_price - current_price) / current_price) * 100

        # Warnings
        low_dividend_warning = None
        if dividend_rate == 0:
            low_dividend_warning = "No dividend - Gordon Model does not apply"
        elif current_price > 0 and (dividend_rate / current_price) < 0.01:
            low_dividend_warning = "Low dividend yield - Gordon Model may not be appropriate"

        # P/E calculations - show P/E even without dividends
        payout_ratio = None
        retention_ratio = None
        theoretical_pe = None

        if eps and eps > 0:
            # Calculate payout ratio if dividends exist
            if dividend_rate > 0:
                payout_ratio = dividend_rate / eps
                retention_ratio = 1 - payout_ratio
                if capm_return > dividend_growth:
                    theoretical_pe = payout_ratio / (capm_return - dividend_growth)

            # Calculate P/E if not already set
            if not pe_ratio:
                pe_ratio = current_price / eps

        result = {
            'ticker': ticker,
            'companyName': company_name,
            'beta': round(float(beta), 3),
            'riskFreeRate': round(float(risk_free_rate), 4),
            'marketReturn': round(float(market_return), 4),
            'currentPrice': round(float(current_price), 2),
            'dividend': round(float(dividend_rate), 2),
            'dividendD1': round(float(d1), 2),
            'dividendGrowth': round(float(dividend_growth), 4),
            'historicalDividendGrowth': round(float(historical_growth), 4) if historical_growth else None,
            'growthWarning': growth_warning,
            'capmReturn': round(float(capm_return), 4),
            'gordonReturn': round(float(gordon_return), 4),
            'fairPrice': round(float(fair_price), 2),
            'valuation': valuation,
            'priceDifference': round(float(price_difference), 2),
            'currency': currency,
            'lowDividendWarning': low_dividend_warning,
            'irregularDividend': False,
            'dividendConsistencyIssues': [],
            'eps': round(float(eps), 2) if eps else None,
            'peRatio': round(float(pe_ratio), 2) if pe_ratio else None,
            'payoutRatio': round(float(payout_ratio), 4) if payout_ratio else None,
            'retentionRatio': round(float(retention_ratio), 4) if retention_ratio else None,
            'roe': None,
            'theoreticalPE': round(float(theoretical_pe), 2) if theoretical_pe else None,
            'sources': {
                'beta': source,
                'riskFreeRate': 'US 10-Year Treasury',
                'marketReturn': 'Historical Average',
                'currentPrice': source,
                'dividend': source,
                'dividendGrowth': 'Calculated from History'
            }
        }

        _cache[cache_key] = result
        print(f"[OK] Processed {ticker} - {valuation}")

        return jsonify(result)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'CAPM API - Render Version',
        'features': ['TradingView data', 'AU/US/VN stocks']
    })

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('.', path)
    except:
        return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("CAPM API - Render Version")
    print("=" * 50)
    app.run(host='0.0.0.0', debug=True, port=port)
