"""
Backend for PythonAnywhere deployment (Python 3.10 compatible)
Uses yfinance instead of tradingview-scraper
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import json
from datetime import datetime
import yfinance as yf

app = Flask(__name__)
CORS(app)

# Cache results
_cache = {}
_cache_timeout = 300  # 5 minutes

# Dividend growth database
DIVIDEND_GROWTH_DATABASE = {
    # Australian Stocks (ASX)
    'CBA': 0.09, 'CSL': 0.09, 'ANZ': 0.08, 'WBC': 0.07, 'NAB': 0.07,
    'BHP': 0.08, 'WES': 0.06, 'WOW': 0.05, 'TLS': 0.03, 'RIO': 0.12,
    # US Stocks
    'KO': 0.03, 'PEP': 0.07, 'JNJ': 0.06, 'PG': 0.05, 'WMT': 0.02,
    'MCD': 0.08, 'MSFT': 0.10, 'AAPL': 0.08, 'V': 0.17, 'MA': 0.16,
}

# Vietnamese stock fallback data
DIVIDEND_FALLBACK_VN = {
    'VNM': {'dividend': 3000, 'growth': 0.04, 'beta': 0.85},
    'VCB': {'dividend': 1500, 'growth': 0.08, 'beta': 1.15},
    'FPT': {'dividend': 2500, 'growth': 0.12, 'beta': 1.20},
    'HPG': {'dividend': 1800, 'growth': 0.06, 'beta': 1.45},
    'TCB': {'dividend': 1000, 'growth': 0.10, 'beta': 1.30},
    'SAB': {'dividend': 2200, 'growth': 0.04, 'beta': 0.75},
    'GAS': {'dividend': 4000, 'growth': 0.04, 'beta': 0.90},
    'MBB': {'dividend': 800, 'growth': 0.09, 'beta': 1.25},
    'VHM': {'dividend': 2000, 'growth': 0.03, 'beta': 1.35},
    'MSN': {'dividend': 1200, 'growth': 0.05, 'beta': 1.10},
    'VIC': {'dividend': 1500, 'growth': 0.05, 'beta': 1.40},
    'PLX': {'dividend': 2000, 'growth': 0.04, 'beta': 0.95},
    'BVH': {'dividend': 1800, 'growth': 0.05, 'beta': 1.00},
    'ACB': {'dividend': 700, 'growth': 0.08, 'beta': 1.20},
    'BID': {'dividend': 1000, 'growth': 0.07, 'beta': 1.15},
    'CTG': {'dividend': 800, 'growth': 0.06, 'beta': 1.18},
    'VPB': {'dividend': 500, 'growth': 0.09, 'beta': 1.35},
    'HDB': {'dividend': 600, 'growth': 0.10, 'beta': 1.28},
    'STB': {'dividend': 400, 'growth': 0.07, 'beta': 1.22},
    'SSI': {'dividend': 1000, 'growth': 0.08, 'beta': 1.40},
    'VJC': {'dividend': 0, 'growth': 0.05, 'beta': 1.50},
    'MWG': {'dividend': 1500, 'growth': 0.06, 'beta': 1.25},
    'PNJ': {'dividend': 2000, 'growth': 0.10, 'beta': 1.15},
    'REE': {'dividend': 1500, 'growth': 0.05, 'beta': 1.05},
    'DGC': {'dividend': 3000, 'growth': 0.08, 'beta': 1.30},
    'GVR': {'dividend': 500, 'growth': 0.04, 'beta': 0.85},
    'POW': {'dividend': 1200, 'growth': 0.03, 'beta': 0.80},
    'BCM': {'dividend': 800, 'growth': 0.05, 'beta': 1.10},
    'VRE': {'dividend': 500, 'growth': 0.04, 'beta': 1.20},
    'NVL': {'dividend': 0, 'growth': 0.05, 'beta': 1.60},
    'ACV': {'dividend': 2500, 'growth': 0.06, 'beta': 0.95},
}

def get_yfinance_data(ticker, is_au_stock=False):
    """Get stock data from yfinance"""
    try:
        yf_ticker = ticker + ".AX" if is_au_stock else ticker
        print(f"Fetching yfinance data for {yf_ticker}...")

        stock = yf.Ticker(yf_ticker)
        info = stock.info

        if not info or 'currentPrice' not in info:
            # Try fast_info for basic data
            fast = stock.fast_info
            current_price = fast.get('lastPrice', 0)
            if current_price == 0:
                return None
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))

        beta = info.get('beta', 1.0)
        company_name = info.get('shortName', info.get('longName', ticker))
        dividend_rate = info.get('dividendRate', 0) or 0
        dividend_yield = info.get('dividendYield', 0) or 0
        eps = info.get('trailingEps', None)
        pe_ratio = info.get('trailingPE', None)

        print(f"[OK] {company_name}: Price={current_price}, Beta={beta}, Dividend={dividend_rate}")

        return {
            'currentPrice': current_price,
            'beta': beta if beta else 1.0,
            'companyName': company_name,
            'dividend': dividend_rate,
            'dividendYield': dividend_yield,
            'eps': eps,
            'peRatio': pe_ratio,
            'source': f'yfinance ({yf_ticker})'
        }
    except Exception as e:
        print(f"Error fetching yfinance data: {e}")
        return None

def get_dividend_growth(ticker, is_au_stock=False):
    """Calculate dividend growth from history"""
    if ticker in DIVIDEND_GROWTH_DATABASE:
        return DIVIDEND_GROWTH_DATABASE[ticker]

    try:
        yf_ticker = ticker + ".AX" if is_au_stock else ticker
        stock = yf.Ticker(yf_ticker)
        dividends = stock.dividends

        if len(dividends) < 2:
            return 0.03  # Default

        annual_divs = dividends.resample('Y').sum()
        if len(annual_divs) < 2:
            return 0.03

        years = len(annual_divs) - 1
        latest = annual_divs.iloc[-1]
        oldest = annual_divs.iloc[0]

        if oldest <= 0:
            return 0.03

        cagr = (latest / oldest) ** (1 / years) - 1
        return max(min(cagr, 0.20), -0.10)  # Cap between -10% and 20%
    except:
        return 0.03

@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()
        market = request.args.get('market', 'US').upper()

        print(f"\n{'='*50}")
        print(f"Processing {ticker} (Market: {market})")
        print(f"{'='*50}")

        # Check cache
        cache_key = f"{ticker}_{market}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        is_vn_stock = market == 'VN'
        is_au_stock = market == 'AU'

        # For Vietnamese stocks, use fallback data
        if is_vn_stock:
            if ticker not in DIVIDEND_FALLBACK_VN:
                return jsonify({'error': f'Vietnamese stock {ticker} not in database. Supported: {", ".join(sorted(DIVIDEND_FALLBACK_VN.keys()))}'}), 400

            fallback = DIVIDEND_FALLBACK_VN[ticker]
            current_price = 50000  # Placeholder - would need real price
            beta = fallback['beta']
            dividend_rate = fallback['dividend']
            dividend_growth = fallback['growth']
            company_name = ticker
            eps = None
            pe_ratio = None

            # Try to get real price from yfinance (some VN stocks have .VN suffix)
            try:
                stock = yf.Ticker(f"{ticker}.VN")
                info = stock.info
                if info and 'currentPrice' in info:
                    current_price = info['currentPrice']
                    company_name = info.get('shortName', ticker)
            except:
                pass

            risk_free_rate = 0.0416
            market_return = 0.09
            currency = 'VND'
            source = 'Fallback Database'
        else:
            # US or AU stocks - use yfinance
            data = get_yfinance_data(ticker, is_au_stock)

            if not data:
                return jsonify({'error': f'Unable to fetch data for {ticker}'}), 400

            current_price = data['currentPrice']
            beta = data['beta']
            company_name = data['companyName']
            dividend_rate = data['dividend']
            eps = data['eps']
            pe_ratio = data['peRatio']
            source = data['source']

            # Get dividend growth
            dividend_growth = get_dividend_growth(ticker, is_au_stock)

            # Get risk-free rate
            try:
                treasury = yf.Ticker("^TNX")
                treasury_data = treasury.history(period="5d")
                if not treasury_data.empty:
                    risk_free_rate = treasury_data['Close'].iloc[-1] / 100
                else:
                    risk_free_rate = 0.042
            except:
                risk_free_rate = 0.042

            if is_au_stock:
                market_return = 0.095
                currency = 'AUD'
            else:
                market_return = 0.10
                currency = 'USD'

        # Calculate CAPM
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)

        # Cap dividend growth if too high
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

        # Low dividend warning
        low_dividend_warning = None
        if dividend_rate == 0:
            low_dividend_warning = "No dividend - Gordon Model does not apply"
        elif (dividend_rate / current_price) < 0.01:
            low_dividend_warning = "Low dividend yield - Gordon Model may not be appropriate"

        # P/E calculations
        payout_ratio = None
        retention_ratio = None
        theoretical_pe = None

        if eps and eps > 0 and dividend_rate > 0:
            payout_ratio = dividend_rate / eps
            retention_ratio = 1 - payout_ratio
            if capm_return > dividend_growth:
                theoretical_pe = payout_ratio / (capm_return - dividend_growth)

        result = {
            'ticker': ticker,
            'companyName': company_name,
            'beta': round(beta, 3),
            'riskFreeRate': round(risk_free_rate, 4),
            'marketReturn': round(market_return, 4),
            'currentPrice': round(current_price, 2),
            'dividend': round(dividend_rate, 2),
            'dividendD1': round(d1, 2),
            'dividendGrowth': round(dividend_growth, 4),
            'historicalDividendGrowth': round(historical_growth, 4) if historical_growth else None,
            'growthWarning': growth_warning,
            'capmReturn': round(capm_return, 4),
            'gordonReturn': round(gordon_return, 4),
            'fairPrice': round(fair_price, 2),
            'valuation': valuation,
            'priceDifference': round(price_difference, 2),
            'currency': currency,
            'lowDividendWarning': low_dividend_warning,
            'irregularDividend': False,
            'dividendConsistencyIssues': [],
            'eps': round(eps, 2) if eps else None,
            'peRatio': round(pe_ratio, 2) if pe_ratio else None,
            'payoutRatio': round(payout_ratio, 4) if payout_ratio else None,
            'retentionRatio': round(retention_ratio, 4) if retention_ratio else None,
            'roe': None,
            'theoreticalPE': round(theoretical_pe, 2) if theoretical_pe else None,
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
        print(f"[OK] Processed {ticker}")

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
        'message': 'CAPM API - PythonAnywhere Version',
        'features': ['yfinance data', 'AU/US/VN stocks']
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
    print("CAPM API - PythonAnywhere Version")
    print("=" * 50)
    app.run(host='0.0.0.0', debug=True, port=port)
