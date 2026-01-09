"""
Enhanced backend with vnstock for Vietnamese stocks
Install: pip install vnstock
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time

app = Flask(__name__)
CORS(app)

# Simple rate limiting - cache results
_cache = {}
_cache_timeout = 60

# Vietnamese stock tickers
VIETNAMESE_STOCKS = ['VNM', 'VCB', 'FPT', 'HPG', 'VHM', 'VIC', 'MSN', 'VRE',
                     'TCB', 'BVH', 'GAS', 'MWG', 'PLX', 'POW', 'SAB', 'SSI',
                     'VJC', 'VPB', 'CTG', 'BID', 'MBB', 'ACB', 'HDB', 'NVL',
                     'VCI', 'PDR', 'VND', 'KDH', 'DIG', 'GEX']

def get_vn_stock_data(ticker):
    """Get Vietnamese stock data using vnstock 3"""
    try:
        from vnstock import Vnstock

        print(f"Fetching Vietnamese stock data for {ticker}...")

        # Initialize vnstock
        stock = Vnstock().stock(symbol=ticker, source='VCI')

        # Get company info
        try:
            company_info = stock.company.profile()
            company_name = company_info.get('name', ticker) if isinstance(company_info, dict) else ticker
        except:
            company_name = ticker

        # Get historical data for price
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        hist_data = stock.quote.history(start=start_date, end=end_date, interval='1D')

        if hist_data is None or hist_data.empty:
            return None

        # Vietnamese stock prices are quoted in thousands of VND
        # vnstock returns them in the quoted format (e.g., 94 means 94,000 VND)
        # Multiply by 1000 to get actual VND amount
        current_price = float(hist_data['close'].iloc[-1]) * 1000

        # Get dividend data - try multiple sources
        dividend_rate = 0.0
        dividend_growth = 0.03
        dividend_source = "Not available"

        # Method 1: Try income statement for dividend info
        try:
            print(f"Attempting to fetch income statement for {ticker}...")
            income_stmt = stock.finance.income_statement(period='year', lang='en', dropna=True)
            if income_stmt is not None and not income_stmt.empty:
                print(f"Income statement columns: {income_stmt.columns.tolist()}")
                # Look for dividend-related columns
                dividend_cols = [col for col in income_stmt.columns if 'dividend' in col.lower()]
                if dividend_cols:
                    print(f"Found dividend columns: {dividend_cols}")
        except Exception as e:
            print(f"Could not fetch income statement: {e}")

        # Method 2: Try cash flow statement
        try:
            print(f"Attempting to fetch cash flow for {ticker}...")
            cash_flow = stock.finance.cash_flow(period='year', dropna=True)
            if cash_flow is not None and not cash_flow.empty:
                print(f"Cash flow columns: {cash_flow.columns.tolist()}")
                # Look for dividend payment in cash flow
                dividend_cols = [col for col in cash_flow.columns if 'dividend' in col.lower() or 'cổ tức' in col.lower()]
                if dividend_cols:
                    print(f"Found dividend payment columns: {dividend_cols}")
                    # Try to extract dividend per share
                    for col in dividend_cols:
                        if cash_flow[col].iloc[0] and cash_flow[col].iloc[0] != 0:
                            # This is total dividend paid, need shares outstanding to get per share
                            print(f"Total dividends paid: {cash_flow[col].iloc[0]}")
        except Exception as e:
            print(f"Could not fetch cash flow: {e}")

        # Method 3: Try financial ratios
        try:
            print(f"Attempting to fetch financial ratios for {ticker}...")
            ratios = stock.finance.ratio(period='year', lang='en')
            if ratios is not None and not ratios.empty:
                print(f"Ratio columns: {ratios.columns.tolist()}")

                # Look for dividend per share or dividend yield
                for col in ratios.columns:
                    if 'dividend' in col.lower():
                        print(f"Found dividend column: {col} = {ratios[col].iloc[0]}")

                if 'dividendPerShare' in ratios.columns:
                    latest_div = ratios['dividendPerShare'].iloc[0]
                    if latest_div and latest_div > 0:
                        # Dividend values are also quoted in thousands VND
                        dividend_rate = float(latest_div) * 1000
                        dividend_source = "vnstock financial ratios (live)"
                        print(f"✓ Found live dividend from ratios: {dividend_rate} VND")

                        # Calculate growth if we have multiple years
                        if len(ratios) >= 2:
                            prev_div = ratios['dividendPerShare'].iloc[1]
                            if prev_div and prev_div > 0:
                                dividend_growth = (latest_div / prev_div) - 1
                                print(f"✓ Calculated dividend growth: {dividend_growth*100:.2f}%")

                # Alternative: Use dividend yield if available
                elif 'dividendYield' in ratios.columns and dividend_rate == 0:
                    div_yield = ratios['dividendYield'].iloc[0]
                    if div_yield and div_yield > 0:
                        # Calculate dividend from yield: Dividend = Price × Yield
                        dividend_rate = current_price * div_yield
                        dividend_source = "Calculated from dividend yield (live)"
                        print(f"✓ Calculated dividend from yield: {dividend_rate} VND")
        except Exception as e:
            print(f"Could not fetch financial ratios: {e}")
            import traceback
            traceback.print_exc()

        # Fallback: For well-known dividend-paying stocks, use approximate values
        # These are stocks with consistent dividend histories suitable for Gordon Model
        DIVIDEND_ESTIMATES = {
            'VNM': {'dividend': 3000.0, 'growth': 0.04},  # Vinamilk - stable dividends
            'VCB': {'dividend': 1500.0, 'growth': 0.08},  # Vietcombank - growing dividends
            'FPT': {'dividend': 2500.0, 'growth': 0.05},  # FPT Corporation
            'HPG': {'dividend': 1800.0, 'growth': 0.06},  # Hoa Phat Group
            'VHM': {'dividend': 2000.0, 'growth': 0.03},  # Vinhomes
            'MSN': {'dividend': 1200.0, 'growth': 0.05},  # Masan Group
            'SAB': {'dividend': 2200.0, 'growth': 0.04},  # Sabeco - stable dividends
            'GAS': {'dividend': 4000.0, 'growth': 0.04},  # PetroVietnam Gas
            'PLX': {'dividend': 1500.0, 'growth': 0.03},  # Petrolimex
            'TCB': {'dividend': 1000.0, 'growth': 0.10},  # Techcombank
            'MBB': {'dividend': 800.0, 'growth': 0.09},   # Military Bank
            'BVH': {'dividend': 1600.0, 'growth': 0.05},  # Bao Viet Holdings
        }

        # Only use estimates as last resort if live data not available
        if dividend_rate == 0 and ticker in DIVIDEND_ESTIMATES:
            dividend_rate = DIVIDEND_ESTIMATES[ticker]['dividend']
            dividend_growth = DIVIDEND_ESTIMATES[ticker]['growth']
            dividend_source = f"Estimated (historical average for {ticker})"
            print(f"⚠ Using estimated dividend for {ticker}: {dividend_rate} VND, growth: {dividend_growth*100}%")
            print(f"   Live data not available - using historical average")
        elif dividend_rate == 0:
            # For other stocks without dividend data, keep at 0
            dividend_rate = 0.0
            dividend_growth = 0.03
            dividend_source = "No dividend data available"
            print(f"⚠ No dividend data found for {ticker}")

        # Get financial ratios for beta estimation (Vietnamese stocks don't have direct beta)
        # We'll use market correlation as approximation
        beta = 1.0  # Default beta for Vietnamese stocks

        # For Vietnamese stocks, use local risk-free rate (Vietnam government bond yield ~3-4%)
        risk_free_rate = 0.035  # 3.5% Vietnam 10-year bond

        # Vietnamese market return (VN-Index historical average ~8-10%)
        market_return = 0.09  # 9% average

        return {
            'ticker': ticker,
            'companyName': company_name,
            'currentPrice': current_price,
            'beta': beta,
            'riskFreeRate': risk_free_rate,
            'marketReturn': market_return,
            'dividend': dividend_rate,
            'dividendGrowth': dividend_growth,
            'source': 'vnstock (VCI)',
            'dividendSource': dividend_source,
            'currency': 'VND'  # Mark as Vietnamese Dong
        }

    except Exception as e:
        print(f"vnstock error for {ticker}: {str(e)}")
        return None

def get_risk_free_rate():
    """Get current US 10-year Treasury yield"""
    try:
        treasury = yf.Ticker("^TNX")
        hist = treasury.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1] / 100
        return 0.045
    except:
        return 0.045

def get_market_return():
    """Get S&P 500 average return"""
    return 0.10  # 10% historical average

def calculate_dividend_growth(stock):
    """Calculate dividend growth rate"""
    try:
        dividends = stock.dividends
        if len(dividends) < 2:
            return 0.03

        years_data = {}
        for date, div in dividends.items():
            year = date.year
            if year not in years_data:
                years_data[year] = 0
            years_data[year] += div

        if len(years_data) < 2:
            return 0.03

        sorted_years = sorted(years_data.keys())
        first_year_div = years_data[sorted_years[0]]
        last_year_div = years_data[sorted_years[-1]]
        years_elapsed = sorted_years[-1] - sorted_years[0]

        if years_elapsed > 0 and first_year_div > 0:
            growth_rate = (last_year_div / first_year_div) ** (1 / years_elapsed) - 1
            return max(min(growth_rate, 0.15), -0.05)
        return 0.03
    except:
        return 0.03

@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()
        original_ticker = ticker

        # Check cache
        cache_key = f"{ticker}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            print(f"Returning cached result for {ticker}")
            return jsonify(_cache[cache_key])

        time.sleep(2)

        # Check if Vietnamese stock
        is_vn_stock = ticker in VIETNAMESE_STOCKS

        if is_vn_stock:
            # Use vnstock for Vietnamese stocks
            vn_data = get_vn_stock_data(ticker)

            if vn_data:
                current_price = vn_data['currentPrice']
                beta = vn_data['beta']
                risk_free_rate = vn_data['riskFreeRate']
                market_return = vn_data['marketReturn']
                dividend_rate = vn_data['dividend']
                dividend_growth = vn_data['dividendGrowth']
                company_name = vn_data['companyName']
                data_source = vn_data['source']
            else:
                return jsonify({'error': f'Unable to fetch data for Vietnamese stock {ticker}'}), 500
        else:
            # Use Yahoo Finance for international stocks
            print(f"Fetching international stock data for {ticker}...")

            import requests
            session = requests.Session()
            session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

            stock = yf.Ticker(ticker, session=session)

            try:
                info = stock.info
            except Exception as e:
                if "Too Many Requests" in str(e) or "429" in str(e):
                    return jsonify({'error': 'Yahoo Finance rate limit exceeded. Please wait and try again.'}), 429
                return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500

            if not info or 'symbol' not in info:
                return jsonify({'error': 'Invalid ticker symbol'}), 400

            company_name = info.get('longName', info.get('shortName', ticker))
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')

            if not current_price:
                hist = stock.history(period="1d")
                if hist.empty:
                    return jsonify({'error': 'Unable to fetch current price'}), 400
                current_price = hist['Close'].iloc[-1]

            beta = info.get('beta', 1.0)
            if not beta or beta <= 0:
                beta = 1.0

            dividend_rate = info.get('dividendRate', 0)
            if dividend_rate == 0:
                dividends = stock.dividends
                if len(dividends) > 0:
                    one_year_ago = datetime.now() - timedelta(days=365)
                    recent_divs = dividends[dividends.index > one_year_ago]
                    dividend_rate = recent_divs.sum() if len(recent_divs) > 0 else 0

            risk_free_rate = get_risk_free_rate()
            market_return = get_market_return()
            dividend_growth = calculate_dividend_growth(stock)
            data_source = 'Yahoo Finance'

        # Calculate CAPM and Gordon Model
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)

        if dividend_rate > 0:
            d1 = dividend_rate * (1 + dividend_growth)
            dividend_yield = d1 / current_price
            gordon_return = dividend_yield + dividend_growth
        else:
            gordon_return = capm_return * 0.8  # Estimate for non-dividend stocks

        if dividend_rate > 0 and (capm_return - dividend_growth) > 0:
            d1 = dividend_rate * (1 + dividend_growth)
            fair_price = d1 / (capm_return - dividend_growth)
        else:
            fair_price = current_price

        valuation = "OVERVALUED" if gordon_return < capm_return else "UNDERVALUED"
        price_difference = ((fair_price - current_price) / current_price) * 100

        result = {
            'ticker': original_ticker,
            'companyName': str(company_name),
            'beta': float(round(beta, 3)),
            'riskFreeRate': float(round(risk_free_rate, 4)),
            'marketReturn': float(round(market_return, 4)),
            'currentPrice': float(round(current_price, 2)),
            'dividend': float(round(dividend_rate, 2)),
            'dividendGrowth': float(round(dividend_growth, 4)),
            'capmReturn': float(round(capm_return, 4)),
            'gordonReturn': float(round(gordon_return, 4)),
            'fairPrice': float(round(fair_price, 2)),
            'valuation': str(valuation),
            'priceDifference': float(round(price_difference, 2)),
            'currency': 'VND' if is_vn_stock else 'USD',
            'sources': {
                'beta': data_source,
                'riskFreeRate': 'VN Gov Bond' if is_vn_stock else 'US 10-Year Treasury',
                'marketReturn': 'VN-Index Historical' if is_vn_stock else 'S&P 500 Historical',
                'currentPrice': data_source,
                'dividend': data_source,
                'dividendGrowth': 'Estimated' if is_vn_stock else 'Calculated from history'
            }
        }

        _cache[cache_key] = result
        print(f"Successfully processed {ticker}")

        return jsonify(result)

    except Exception as e:
        print(f"Error processing {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process ticker: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'CAPM API with vnstock support',
        'features': ['Vietnamese stocks via vnstock', 'International stocks via Yahoo Finance']
    })

if __name__ == '__main__':
    print("=" * 60)
    print("CAPM & Gordon Model API - Enhanced Version")
    print("=" * 60)
    print("Features:")
    print("  - Vietnamese stocks: vnstock (VCI data)")
    print("  - International stocks: Yahoo Finance")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    app.run(debug=True, port=5000)
