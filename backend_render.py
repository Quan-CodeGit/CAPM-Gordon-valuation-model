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
from damodaran_db import (
    init_db, get_industries, get_benchmark, get_config,
    calculate_industry_growth, update_damodaran_data, get_damodaran_status,
    refresh_regional_data,
)

ADMIN_KEY = os.environ.get('ADMIN_KEY', 'dev-key-change-in-production')

app = Flask(__name__)
CORS(app)
init_db()

# ── Startup: download regional Damodaran Excel files in background ──────────
# Non-blocking — app starts serving requests immediately; data loads in ~30s.
import threading

def _startup_damodaran_refresh():
    try:
        report = refresh_regional_data()
        totals = {r: {d: v['count'] for d, v in ds.items()}
                  for r, ds in report.items()}
        print(f'[STARTUP] Damodaran regional refresh complete: {totals}')
    except Exception as e:
        print(f'[STARTUP] Damodaran regional refresh failed (non-fatal): {e}')

threading.Thread(target=_startup_damodaran_refresh, daemon=True).start()

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

def map_tv_to_damodaran(sector, industry):
    """Map TradingView sector/industry strings to the nearest Damodaran industry name.
    Uses case-insensitive substring matching; most-specific checks come first.
    Returns None if no match found (caller falls back to historical growth).
    """
    s = f"{industry or ''} {sector or ''}".lower().strip()
    if not s:
        return None

    # ---- Banking & Finance ----
    if any(x in s for x in ['money center', 'bulge bracket']):
        return 'Bank (Money Center)'
    if any(x in s for x in ['major bank', 'regional bank', 'diversified bank', 'commercial bank', 'retail bank']):
        return 'Banks (Regional)'
    if 'bank' in s and 'investment bank' not in s:
        return 'Banks (Regional)'
    if any(x in s for x in ['investment bank', 'brokerage', 'capital market']):
        return 'Brokerage & Investment Banking'
    if any(x in s for x in ['life insurance', 'life & health insurance']):
        return 'Insurance (Life)'
    if any(x in s for x in ['property insurance', 'casualty insurance', 'p&c insurance', 'prop/cas']):
        return 'Insurance (Prop/Cas.)'
    if 'insurance' in s:
        return 'Insurance (General)'
    if any(x in s for x in ['investment manager', 'asset management', 'fund management', 'wealth management']):
        return 'Investments & Asset Management'
    if any(x in s for x in ['financial service', 'diversified financial', 'consumer finance', 'credit service', 'payment']):
        return 'Financial Svcs. (Non-bank & Insurance)'

    # ---- Technology ----
    if any(x in s for x in ['semiconductor equipment', 'semiconductor equip']):
        return 'Semiconductor Equip'
    if 'semiconductor' in s:
        return 'Semiconductor'
    if any(x in s for x in ['internet software', 'software internet', 'saas', 'cloud software']):
        return 'Software (Internet)'
    if any(x in s for x in ['entertainment software', 'video game', 'gaming software']):
        return 'Software (Entertainment)'
    if 'software' in s:
        return 'Software (System & Application)'
    if any(x in s for x in ['computer hardware', 'technology hardware', 'computer & peripheral', 'computers/peripheral']):
        return 'Computers/Peripherals'
    if any(x in s for x in ['it service', 'computer service', 'information technology service']):
        return 'Computer Services'
    if any(x in s for x in ['electronic equipment', 'electronic component']):
        return 'Electronics (General)'
    if any(x in s for x in ['consumer electronic', 'office electronic']):
        return 'Electronics (Consumer & Office)'
    if any(x in s for x in ['telecom equipment', 'communication equipment']):
        return 'Telecom. Equipment'
    if any(x in s for x in ['wireless telecom', 'telecom wireless', 'mobile telecom']):
        return 'Telecom (Wireless)'
    if any(x in s for x in ['telecom', 'telecommunication', 'integrated telecom']):
        return 'Telecom. Services'

    # ---- Healthcare ----
    if any(x in s for x in ['drug biotech', 'drugs biotech', 'biotechnology', 'biotech']):
        return 'Drugs (Biotechnology)'
    if any(x in s for x in ['drug pharma', 'drugs pharma', 'pharmaceutical', 'pharma']):
        return 'Drugs (Pharmaceutical)'
    if any(x in s for x in ['medical device', 'medical equipment']):
        return 'Healthcare Products'
    if any(x in s for x in ['health information', 'healthcare information', 'health technology']):
        return 'Healthcare Information and Technology'
    if any(x in s for x in ['hospital', 'health care facilit', 'healthcare facilit']):
        return 'Hospitals/Healthcare Facilities'
    if any(x in s for x in ['health care service', 'healthcare service', 'managed care', 'managed health']):
        return 'Healthcare Support Services'
    if any(x in s for x in ['health care product', 'healthcare product', 'health product', 'medical supply']):
        return 'Healthcare Products'

    # ---- Energy ----
    if any(x in s for x in ['coal']):
        return 'Coal & Related Energy'
    if any(x in s for x in ['oilfield service', 'oil service', 'oil equipment', 'drilling']):
        return 'Oilfield Svcs/Equip.'
    if any(x in s for x in ['oil gas distribution', 'pipeline', 'midstream']):
        return 'Oil/Gas Distribution'
    if any(x in s for x in ['exploration', 'production', 'upstream', 'e&p', 'independent oil']):
        return 'Oil/Gas (Production and Exploration)'
    if any(x in s for x in ['oil', 'gas', 'petroleum', 'integrated energy']):
        return 'Oil/Gas (Integrated)'
    if any(x in s for x in ['renewable energy', 'solar', 'wind energy', 'green energy']):
        return 'Green & Renewable Energy'
    if any(x in s for x in ['power', 'electric utility', 'electric power']):
        return 'Power'
    if any(x in s for x in ['water utility', 'water util']):
        return 'Utility (Water)'
    if any(x in s for x in ['utility', 'utilities', 'gas utility', 'multi-util']):
        return 'Utility (General)'

    # ---- Materials ----
    if any(x in s for x in ['gold', 'precious metal', 'silver', 'platinum']):
        return 'Precious Metals'
    if 'steel' in s:
        return 'Steel'
    if any(x in s for x in ['metal', 'mining', 'iron ore', 'alumin', 'copper', 'zinc', 'nickel']):
        return 'Metals & Mining'
    if any(x in s for x in ['specialty chemical', 'speciality chemical']):
        return 'Chemical (Specialty)'
    if any(x in s for x in ['diversified chemical']):
        return 'Chemical (Diversified)'
    if 'chemical' in s:
        return 'Chemical (Basic)'
    if any(x in s for x in ['paper', 'forest product', 'lumber', 'pulp']):
        return 'Paper/Forest Products'
    if any(x in s for x in ['packaging', 'container']):
        return 'Packaging & Container'
    if any(x in s for x in ['construction material', 'building material', 'building product', 'construction supply']):
        return 'Building Materials'

    # ---- Real Estate ----
    if any(x in s for x in ['retail reit', 'office reit', 'industrial reit', 'residential reit', 'diversified reit', 'r.e.i.t', 'real estate investment trust']):
        return 'R.E.I.T.'
    if any(x in s for x in ['real estate develop', 'homebuil', 'home build']):
        return 'Real Estate (Development)'
    if any(x in s for x in ['real estate operation', 'real estate service']):
        return 'Real Estate (Operations & Services)'
    if any(x in s for x in ['real estate']):
        return 'Real Estate (General/Diversified)'

    # ---- Consumer ----
    if any(x in s for x in ['alcoholic beverage', 'beer', 'wine', 'spirits', 'distill']):
        return 'Beverage (Alcoholic)'
    if any(x in s for x in ['soft drink', 'nonalcoholic', 'non-alcoholic beverage', 'beverage']):
        return 'Beverage (Soft)'
    if 'tobacco' in s:
        return 'Tobacco'
    if any(x in s for x in ['food process', 'food product', 'packaged food', 'food manufactur']):
        return 'Food Processing'
    if any(x in s for x in ['food wholesale', 'grocery wholesale', 'food distribut']):
        return 'Food Wholesalers'
    if any(x in s for x in ['restaurant', 'dining', 'fast food', 'food service']):
        return 'Restaurant/Dining'
    if any(x in s for x in ['household product', 'personal care', 'personal product', 'home product']):
        return 'Household Products'
    if any(x in s for x in ['apparel', 'textile', 'luxury good', 'fashion', 'clothing', 'footwear']):
        return 'Apparel'
    if any(x in s for x in ['home furnish', 'furniture', 'home decor']):
        return 'Furn/Home Furnishings'
    if any(x in s for x in ['auto part', 'automobile part']):
        return 'Auto Parts'
    if any(x in s for x in ['automobile', 'auto manufacturer', 'car manufacturer', 'vehicle']):
        return 'Auto & Truck'
    if any(x in s for x in ['retail auto', 'car dealer']):
        return 'Retail (Automotive)'
    if any(x in s for x in ['home improvement', 'building supply retail', 'home center']):
        return 'Retail (Building Supply)'
    if any(x in s for x in ['grocery', 'food retail', 'supermarket', 'food store']):
        return 'Retail (Grocery and Food)'
    if any(x in s for x in ['specialty retail', 'special line']):
        return 'Retail (Special Lines)'
    if any(x in s for x in ['broadline retail', 'general retail', 'department store', 'mass merchant']):
        return 'Retail (General)'
    if any(x in s for x in ['internet retail', 'online retail', 'e-commerce', 'ecommerce']):
        return 'Retail (General)'
    if 'retail' in s:
        return 'Retail (General)'
    if any(x in s for x in ['hotel', 'gaming', 'casino', 'resort', 'lodging', 'hospitality']):
        return 'Hotel/Gaming'
    if any(x in s for x in ['recreation', 'leisure', 'sport']):
        return 'Recreation'

    # ---- Media & Entertainment ----
    if any(x in s for x in ['publishing', 'newspaper', 'magazine']):
        return 'Publishing & Newspapers'
    if any(x in s for x in ['broadcast', 'radio', 'television']):
        return 'Broadcasting'
    if any(x in s for x in ['cable']):
        return 'Cable TV'
    if any(x in s for x in ['media', 'entertainment', 'movie', 'film', 'streaming']):
        return 'Entertainment'
    if any(x in s for x in ['advertising', 'marketing service']):
        return 'Advertising'

    # ---- Industrials ----
    if any(x in s for x in ['aerospace', 'defense', 'defence']):
        return 'Aerospace/Defense'
    if any(x in s for x in ['airline', 'air transport']):
        return 'Air Transport'
    if any(x in s for x in ['railroad', 'rail transport']):
        return 'Transportation (Railroads)'
    if 'trucking' in s:
        return 'Trucking'
    if any(x in s for x in ['transport', 'shipping', 'logistic', 'freight']):
        return 'Transportation'
    if any(x in s for x in ['engineering', 'construction']):
        return 'Engineering/Construction'
    if any(x in s for x in ['electrical equipment', 'electric equipment']):
        return 'Electrical Equipment'
    if any(x in s for x in ['machinery', 'machine tool', 'industrial machine']):
        return 'Machinery'
    if any(x in s for x in ['office equipment', 'office service']):
        return 'Office Equipment & Services'
    if any(x in s for x in ['environment', 'waste', 'water treatment']):
        return 'Environmental & Waste Services'
    if any(x in s for x in ['farm', 'agricult', 'crop']):
        return 'Farming/Agriculture'
    if any(x in s for x in ['business service', 'consumer service']):
        return 'Business & Consumer Services'
    if any(x in s for x in ['information service', 'data service']):
        return 'Information Services'
    if any(x in s for x in ['education', 'school', 'university', 'training']):
        return 'Education'

    # ---- Broad sector fallbacks ----
    if any(x in s for x in ['finance', 'financial']):
        return 'Financial Svcs. (Non-bank & Insurance)'
    if any(x in s for x in ['technology', 'tech']):
        return 'Software (System & Application)'
    if any(x in s for x in ['health', 'medical']):
        return 'Healthcare Products'
    if any(x in s for x in ['consumer discretionary', 'consumer cyclical']):
        return 'Retail (General)'
    if any(x in s for x in ['consumer staple', 'consumer defensive']):
        return 'Food Processing'
    if any(x in s for x in ['industrial']):
        return 'Machinery'
    if any(x in s for x in ['material', 'basic material']):
        return 'Metals & Mining'
    if any(x in s for x in ['communicat', 'comm. service']):
        return 'Telecom. Services'

    return None


def suggest_damodaran_industries(tv_sector, tv_industry, n=5):
    """
    Return top-N Damodaran industry names closest to the given TradingView
    sector/industry strings, using token-overlap scoring.
    Falls back to empty list if there is no meaningful input.
    """
    import re
    from damodaran_db import get_industries

    raw = f"{tv_industry or ''} {tv_sector or ''}".lower()
    stop = {'and', 'or', 'the', 'of', 'for', 'in', 'a', 'an', 'to', 'with',
            'at', 'by', 'from', 'as', 'is', 'are', 'its', 'it', 'be', 'was'}
    tokens = set(re.findall(r'[a-z]+', raw)) - stop
    if not tokens:
        return []

    industries = get_industries()
    scores = []
    for ind in industries:
        name = ind['industry_name']
        name_lower = name.lower()
        name_tokens = set(re.findall(r'[a-z]+', name_lower)) - stop
        # Exact token matches (weighted 2) + substring containment (weighted 1)
        exact = len(tokens & name_tokens)
        partial = sum(1 for t in tokens if len(t) > 3 and t in name_lower)
        score = exact * 2 + partial
        if score > 0:
            scores.append((score, name))

    scores.sort(key=lambda x: -x[0])
    return [name for _, name in scores[:n]]


def get_tradingview_data(ticker, is_vn_stock=False, is_au_stock=False):
    """Fetch stock data from TradingView"""
    try:
        from tradingview_scraper.symbols.overview import Overview

        if is_vn_stock:
            exchanges = ['HOSE', 'HNX', 'UPCOM']
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

        # Debug: log all key field groups for VN stocks (covers HOSE / HNX / UPCOM)
        if is_vn_stock:
            eps_fields  = {k: data.get(k) for k in data.keys() if 'eps' in k.lower() or 'earning' in k.lower()}
            pe_fields   = {k: data.get(k) for k in data.keys() if 'p/e' in k.lower() or 'pe' in k.lower() or 'price_earning' in k.lower()}
            beta_fields = {k: data.get(k) for k in data.keys() if 'beta' in k.lower()}
            div_fields  = {k: data.get(k) for k in data.keys() if 'div' in k.lower() or 'yield' in k.lower()}
            print(f"[DEBUG TV] {ticker} ({exchange}) beta fields : {beta_fields}")
            print(f"[DEBUG TV] {ticker} ({exchange}) EPS fields  : {eps_fields}")
            print(f"[DEBUG TV] {ticker} ({exchange}) P/E fields  : {pe_fields}")
            print(f"[DEBUG TV] {ticker} ({exchange}) div fields  : {div_fields}")

        # Extract sector/industry classification from TradingView
        tv_sector = data.get('sector', None) or data.get('type_specific', None)
        tv_industry = (
            data.get('industry', None)
            or data.get('industry_group', None)
            or data.get('subtype', None)
        )
        print(f"[DEBUG TV] {ticker} sector={tv_sector!r}, industry={tv_industry!r}")

        current_price = data.get('close', 0)
        company_name = data.get('description', ticker)

        # ── Beta ──────────────────────────────────────────────────────────────
        # TradingView returns 0.0 (not None) for thinly-traded UPCOM/HNX stocks.
        # Fallback chain: beta_1_year → beta_5_year → beta_3_year → beta → 1.0
        beta_raw = (data.get('beta_1_year') or data.get('beta_5_year') or
                    data.get('beta_3_year') or data.get('beta'))
        try:
            beta_val = float(beta_raw) if beta_raw else 0.0
            if beta_val > 0:
                beta = beta_val
                beta_estimated = False
            else:
                beta = 1.0
                beta_estimated = True   # no real beta data — using market-average assumption
        except (ValueError, TypeError):
            beta = 1.0
            beta_estimated = True

        # ── Dividend ──────────────────────────────────────────────────────────
        dividend_yield_percent = data.get('dividends_yield') or 0
        div_per_share_fy = data.get('dividends_per_share_fy', None)
        pe_ratio = data.get('price_earnings_ttm', None)

        # ── EPS ───────────────────────────────────────────────────────────────
        # IMPORTANT: For VN stocks TradingView returns EPS in USD → must convert to VND later.
        eps_diluted_ttm = data.get('earnings_per_share_diluted_ttm', None)
        eps_basic_ttm   = data.get('earnings_per_share_basic_ttm', None)
        eps_fq          = data.get('earnings_per_share_fq', None)
        eps_fy          = data.get('earnings_per_share_diluted_fy', None) or data.get('earnings_per_share_basic_fy', None)

        if is_vn_stock:
            # Try TTM first (diluted > basic), then FY, then quarterly — all in USD
            candidates = [v for v in [eps_diluted_ttm, eps_basic_ttm, eps_fy, eps_fq] if v and float(v) > 0]
            eps = float(max(candidates)) if candidates else None
            print(f"[DEBUG TV] {ticker} EPS (USD): diluted={eps_diluted_ttm}, basic={eps_basic_ttm}, fy={eps_fy}, fq={eps_fq} → chosen={eps}")
        else:
            eps = eps_diluted_ttm or eps_basic_ttm or eps_fq

        dividend_yield = float(dividend_yield_percent) / 100 if dividend_yield_percent else 0

        if div_per_share_fy and float(div_per_share_fy) > 0:
            dividend_rate = float(div_per_share_fy)
            has_fy_dividend = True
        else:
            dividend_rate = current_price * dividend_yield if dividend_yield else 0
            has_fy_dividend = False

        return {
            'currentPrice': current_price,
            'beta': beta,
            'betaEstimated': beta_estimated,   # True = no real beta; 1.0 is market-avg assumption
            'companyName': company_name,
            'dividend': dividend_rate,
            'hasFYDividend': has_fy_dividend,
            'dividendYield': dividend_yield,
            'peRatio': pe_ratio,
            'eps': eps,                         # None = unavailable; negative = loss-making
            'source': f'TradingView ({exchange}:{ticker})',
            'tvSector': tv_sector,
            'tvIndustry': tv_industry,
        }
    except Exception as e:
        print(f"TradingView error for {ticker}: {e}")
        return None

def get_ttm_dividend(ticker, is_au_stock=False):
    """
    Get annual dividend from yfinance by detecting payment frequency and
    taking exactly the right number of most-recent payments.
      Quarterly → last 4 payments
      Semi-annual → last 2 payments
      Annual → last 1 payment
    This avoids the 5-payment over-count that occurs when a 13-month window
    straddles two calendar years for quarterly payers.
    """
    try:
        import yfinance as yf

        yf_ticker = ticker + ".AX" if is_au_stock else ticker
        stock = yf.Ticker(yf_ticker)
        dividends = stock.dividends

        if dividends is None or len(dividends) == 0:
            return None

        # Detect frequency from the median gap between recent payments
        recent_all = dividends.tail(8)
        if len(recent_all) >= 2:
            gaps = recent_all.index.to_series().diff().dropna().dt.days
            median_gap = gaps.median()
        else:
            median_gap = 90  # assume quarterly

        if median_gap <= 50:
            payments_per_year = 12   # monthly
        elif median_gap <= 110:
            payments_per_year = 4    # quarterly
        elif median_gap <= 200:
            payments_per_year = 2    # semi-annual
        else:
            payments_per_year = 1    # annual

        last_n = dividends.tail(payments_per_year)
        annual_div = float(last_n.sum())
        print(f"[DIVIDEND] {ticker} annual dividend: {annual_div:.4f} "
              f"(last {payments_per_year} payments, median gap {median_gap:.0f}d)")
        return annual_div

    except Exception as e:
        print(f"[DIVIDEND] yfinance failed for {ticker}: {e}")
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

def get_risk_free_rate(market='US'):
    """
    Fetch the 10-year government bond yield for the given market from TradingView (TVC).
      US  → TVC:US10Y   (fallback: yfinance ^TNX, then 0.042)
      AU  → TVC:AU10Y   (fallback: 0.045)
      VN  → TVC:VN10Y   (fallback: 0.040)
    Returns a decimal (e.g. 0.0494 for 4.94%).
    """
    FALLBACKS = {'US': 0.042, 'AU': 0.045, 'VN': 0.040}
    TVC_SYMBOLS = {'US': 'TVC:US10Y', 'AU': 'TVC:AU10Y', 'VN': 'TVC:VN10Y'}

    # 1. Try TradingView TVC bond
    try:
        from tradingview_scraper.symbols.overview import Overview
        symbol = TVC_SYMBOLS.get(market, 'TVC:US10Y')
        overview = Overview()
        result = overview.get_symbol_overview(symbol=symbol)
        if result and 'data' in result:
            close = result['data'].get('close') or result['data'].get('last_bar_close')
            if close and float(close) > 0:
                rate = float(close) / 100   # TVC yields are in % (e.g. 4.937 → 0.04937)
                print(f"[RFR] {symbol} = {rate*100:.3f}% (TradingView TVC)")
                return rate
    except Exception as e:
        print(f"[RFR] TradingView TVC fetch failed for {market}: {e}")

    # 2. US fallback: yfinance ^TNX
    if market == 'US':
        try:
            import yfinance as yf
            treasury = yf.Ticker("^TNX")
            data = treasury.history(period="5d")
            if not data.empty:
                rate = data['Close'].iloc[-1] / 100
                print(f"[RFR] ^TNX (yfinance) = {rate*100:.3f}%")
                return rate
        except Exception as e:
            print(f"[RFR] yfinance ^TNX fallback failed: {e}")

    fallback = FALLBACKS.get(market, 0.042)
    print(f"[RFR] Using hardcoded fallback for {market}: {fallback*100:.2f}%")
    return fallback

def _require_admin_key():
    key = request.headers.get('X-Admin-Key', '')
    if key != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return None


@app.route('/api/damodaran-status', methods=['GET'])
def damodaran_status_public():
    """
    Public endpoint — no auth required.
    Shows whether regional Damodaran data (VN/AU/US fundgr + histgr) has loaded.
    Visit /api/damodaran-status to diagnose download failures.
    """
    try:
        status = get_damodaran_status()
        # Summarise regional table per region/dataset
        regional = {}
        for row in status.get('regional_datasets', []):
            key = f"{row['region']}/{row['dataset']}"
            regional[key] = {'rows': row['cnt'], 'last_updated': row['lu']}

        total_regional = sum(r['rows'] for r in regional.values())
        return jsonify({
            'legacy_us_industries': status['industry_count'],
            'regional_data_loaded': total_regional > 0,
            'regional_total_rows': total_regional,
            'regional_breakdown': regional,
            'source_year': status['source_year'],
            'last_updated': status['last_updated'],
            'note': (
                'Regional data loaded ✓' if total_regional > 0
                else 'Regional data NOT loaded — startup download may have failed. '
                     'Check server logs or POST /api/admin/refresh-damodaran.'
            ),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/industries', methods=['GET'])
def list_industries():
    """Return all Damodaran industries for the frontend dropdown."""
    try:
        rows = get_industries()
        return jsonify({'industries': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/growth-rate', methods=['GET'])
def get_growth_rate():
    """Calculate industry-adjusted g for a given industry and currency."""
    industry = request.args.get('industry', '').strip()
    currency = request.args.get('currency', 'USD').upper()
    if not industry:
        return jsonify({'error': 'industry parameter required'}), 400
    try:
        result = calculate_industry_growth(industry, currency)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/damodaran-status', methods=['GET'])
def damodaran_status():
    auth_err = _require_admin_key()
    if auth_err:
        return auth_err
    try:
        return jsonify(get_damodaran_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/update-damodaran', methods=['POST'])
def update_damodaran():
    auth_err = _require_admin_key()
    if auth_err:
        return auth_err
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        result = update_damodaran_data(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/refresh-damodaran', methods=['POST'])
def admin_refresh_damodaran():
    """
    Download and cache all 6 Damodaran regional Excel files:
      US / Australia / Emerging  ×  fundamental (fundgr) / historical (histgr)
    Requires X-Admin-Key header.
    """
    auth_err = _require_admin_key()
    if auth_err:
        return auth_err
    try:
        report = refresh_regional_data()
        totals = {r: {d: v for d, v in ds.items()} for r, ds in report.items()}
        return jsonify({'status': 'ok', 'report': totals})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/valuation/<ticker>', methods=['GET'])
def get_valuation(ticker):
    try:
        ticker = ticker.upper()
        market = request.args.get('market', 'US').upper()

        print(f"\n{'='*50}")
        print(f"Processing {ticker} (Market: {market})")
        print(f"{'='*50}")

        industry = request.args.get('industry', '').strip()
        growth_override_param = request.args.get('growth_override', '').strip()
        cache_key = f"{ticker}_{market}_{industry}_{growth_override_param}_{int(time.time() / _cache_timeout)}"
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        is_vn_stock = market == 'VN'
        is_au_stock = market == 'AU'
        tv_data = None  # initialise; set in each branch below

        # Vietnamese stocks - try TradingView first, fallback if fails
        if is_vn_stock:
            tv_data = get_tradingview_data(ticker, is_vn_stock=True)

            if tv_data and tv_data['currentPrice'] > 0:
                # Use TradingView data
                current_price = tv_data['currentPrice']
                beta = tv_data['beta']
                beta_estimated = tv_data.get('betaEstimated', False)
                company_name = tv_data['companyName']
                source = tv_data['source']

                # For VN stocks, dividend is calculated from yield × close price (both in VND)
                # div_per_share_fy is always None for VN stocks, so yield-based calc is used
                # No conversion needed since close is already in VND
                dividend_rate = tv_data['dividend']

                # Get EPS in VND and P/E from TradingView
                # - P/E from TradingView is correct (currency-neutral) → use directly
                # - EPS from TradingView is in USD → convert to VND
                # Method 1: If P/E available, use P/E directly + derive EPS = Price / P/E
                # Method 2: Convert raw EPS from USD to VND using exchange rate
                tv_pe = tv_data['peRatio']
                raw_eps = tv_data['eps']  # EPS in USD

                if tv_pe and tv_pe > 0 and current_price > 0:
                    pe_ratio = tv_pe
                    eps = current_price / tv_pe
                    print(f"[DEBUG] {ticker} P/E={tv_pe:.2f}, EPS={eps:.0f} VND (from Price/P/E)")
                elif raw_eps and raw_eps > 0:
                    usd_vnd_rate = get_usd_vnd_rate()
                    eps = raw_eps * usd_vnd_rate
                    pe_ratio = current_price / eps if eps > 0 else None
                    print(f"[DEBUG] {ticker} EPS={eps:.0f} VND (from {raw_eps:.4f} USD × {usd_vnd_rate})" + (f", P/E={pe_ratio:.2f}" if pe_ratio else ""))
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
                beta_estimated = True   # fallback DB beta — treat as estimated
                dividend_rate = fallback['dividend']
                dividend_growth = fallback['growth']
                company_name = fallback['name']
                eps = None
                pe_ratio = None
                source = 'Fallback Database (TradingView unavailable)'
            else:
                return jsonify({'error': f'Stock {ticker} not found on TradingView or in database'}), 400

            risk_free_rate = get_risk_free_rate('VN')
            market_return = 0.09
            currency = 'VND'
        else:
            # US/AU stocks - use TradingView
            tv_data = get_tradingview_data(ticker, is_vn_stock=False, is_au_stock=is_au_stock)

            if not tv_data:
                return jsonify({'error': f'Unable to fetch data for {ticker}'}), 400

            current_price = tv_data['currentPrice']
            beta = tv_data['beta']
            beta_estimated = tv_data.get('betaEstimated', False)
            company_name = tv_data['companyName']
            source = tv_data['source']

            # Dividend source priority:
            # 1. TradingView dividends_per_share_fy — actual FY annual (most accurate, matches TV chart)
            # 2. yfinance TTM sum — only used when TV has no FY data (falls back to yield × price estimate)
            if tv_data.get('hasFYDividend'):
                dividend_rate = tv_data['dividend']
                print(f"[DEBUG] {ticker} Using TradingView FY dividend: {dividend_rate:.4f}")
            else:
                ttm_div = get_ttm_dividend(ticker, is_au_stock)
                if ttm_div and ttm_div > 0:
                    dividend_rate = ttm_div
                    print(f"[DEBUG] {ticker} Using yfinance TTM dividend (TV had no FY data): {dividend_rate:.4f}")
                else:
                    dividend_rate = tv_data['dividend']
                    print(f"[DEBUG] {ticker} Using TradingView dividend (yield × price fallback): {dividend_rate:.4f}")

            # Get EPS and P/E from TradingView
            # - P/E from TradingView is always correct (currency-neutral) → use directly
            # - EPS from TradingView is in USD for ALL markets
            #   - US stocks: USD is correct, use raw EPS directly
            #   - AU stocks: need AUD, derive EPS = Price / P/E
            tv_pe = tv_data['peRatio']
            raw_eps = tv_data['eps']  # Always in USD

            if is_au_stock:
                # AU: raw EPS is in USD, need AUD → derive from P/E
                if tv_pe and tv_pe > 0 and current_price > 0:
                    eps = current_price / tv_pe
                    pe_ratio = tv_pe
                    print(f"[DEBUG] {ticker} EPS from P/E: {current_price} / {tv_pe:.2f} = A${eps:.2f}")
                elif raw_eps and raw_eps > 0:
                    eps = raw_eps  # USD fallback (not ideal but better than nothing)
                    pe_ratio = current_price / eps if eps > 0 else None
                    print(f"[DEBUG] {ticker} EPS fallback (USD): {eps:.2f}")
                else:
                    eps = None
                    pe_ratio = None
            else:
                # US: raw EPS is already in USD, use directly
                # Use TradingView P/E directly (don't recalculate from live price)
                if raw_eps and raw_eps > 0:
                    eps = raw_eps
                    pe_ratio = tv_pe if tv_pe else (current_price / eps if eps > 0 else None)
                    print(f"[DEBUG] {ticker} EPS: ${eps:.2f}, P/E: {pe_ratio:.2f}" if pe_ratio else f"[DEBUG] {ticker} EPS: ${eps:.2f}")
                elif tv_pe and tv_pe > 0 and current_price > 0:
                    eps = current_price / tv_pe
                    pe_ratio = tv_pe
                    print(f"[DEBUG] {ticker} EPS from P/E: ${eps:.2f}")
                else:
                    eps = None
                    pe_ratio = None

            dividend_growth = get_dividend_growth(ticker, is_au_stock)
            risk_free_rate = get_risk_free_rate('AU' if is_au_stock else 'US')

            if is_au_stock:
                market_return = 0.095
                currency = 'AUD'
            else:
                market_return = 0.10
                currency = 'USD'

        # Industry-adjusted growth rate (Damodaran methodology)
        # Priority: 1) manual growth_override, 2) ?industry= param, 3) auto from TradingView sector
        industry_growth_info = None
        auto_detected_industry = None
        industry_suggestions = []
        raw_tv_sector = tv_data.get('tvSector') if tv_data else None
        raw_tv_industry = tv_data.get('tvIndustry') if tv_data else None

        if growth_override_param:
            try:
                override_val = float(growth_override_param)
                if 0.0 <= override_val <= 0.20:
                    dividend_growth = override_val
                    industry_growth_info = {
                        'method': 'override',
                        'source': f'Manual override ({override_val*100:.2f}%)',
                        'note': None, 'capped': False
                    }
            except ValueError:
                pass
        else:
            # Determine which industry to use (manual param or auto-detected from TV)
            effective_industry = industry
            if not effective_industry:
                # Auto-detect from TradingView sector/industry fields
                effective_industry = map_tv_to_damodaran(raw_tv_sector, raw_tv_industry)
                auto_detected_industry = effective_industry
                if effective_industry:
                    print(f"[AUTO] {ticker}: TV sector={raw_tv_sector!r}, industry={raw_tv_industry!r} → Damodaran={effective_industry!r}")
                else:
                    print(f"[AUTO] {ticker}: No sector match, computing suggestions")
                    industry_suggestions = suggest_damodaran_industries(raw_tv_sector, raw_tv_industry)
                    print(f"[SUGGEST] {ticker}: {industry_suggestions}")

            if effective_industry:
                ig = calculate_industry_growth(effective_industry, currency)
                ig['method'] = 'industry'
                ig['industryName'] = effective_industry
                ig['autoDetected'] = (effective_industry == auto_detected_industry)
                dividend_growth = ig['g']
                industry_growth_info = ig

        # Calculate CAPM
        capm_return = risk_free_rate + beta * (market_return - risk_free_rate)

        # Cap dividend growth if needed (skip for manual override — user-intentional)
        growth_warning = None
        historical_growth = dividend_growth
        is_override = industry_growth_info and industry_growth_info.get('method') == 'override'
        if not is_override and dividend_growth >= capm_return - 0.01:
            historical_growth = dividend_growth
            dividend_growth = min(capm_return - 0.01, max(capm_return - 0.03, 0.03))
            growth_warning = f"Growth capped from {historical_growth*100:.1f}% to {dividend_growth*100:.1f}% (g must be < CAPM return)"

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
            'betaEstimated': beta_estimated,
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
            'growthDetails': {
                'method':       industry_growth_info.get('method', 'historical'),
                'industryName': industry_growth_info.get('industryName') if industry_growth_info else None,
                # Raw g values (before CAPM safety cap)
                'g':            industry_growth_info.get('g')            if industry_growth_info else None,
                'earningsYieldGrowth': industry_growth_info.get('earnings_yield_g') if industry_growth_info else None,
                # Gordon DDM tier breakdown (fundgr / ROE×b)
                'industryEpsGrowth':  industry_growth_info.get('industry_eps_growth')  if industry_growth_info else None,
                'benchmarkEpsGrowth': industry_growth_info.get('benchmark_eps_growth') if industry_growth_info else None,
                'tier':               industry_growth_info.get('tier')                 if industry_growth_info else None,
                'ratio':              industry_growth_info.get('ratio')                if industry_growth_info else None,
                'effectiveBenchmark': industry_growth_info.get('effective_benchmark')  if industry_growth_info else None,
                'capMult':            industry_growth_info.get('cap_mult')             if industry_growth_info else None,
                'capPct':             industry_growth_info.get('cap_pct')              if industry_growth_info else None,
                # EY tier breakdown (histgr / 5yr EPS)
                'industryHistGrowth':        industry_growth_info.get('industry_hist_growth')    if industry_growth_info else None,
                'benchmarkHistGrowth':       industry_growth_info.get('benchmark_hist_growth')   if industry_growth_info else None,
                'eyTier':                    industry_growth_info.get('ey_tier')                 if industry_growth_info else None,
                'eyRatio':                   industry_growth_info.get('ey_ratio')                if industry_growth_info else None,
                'eyEffectiveBenchmark':      industry_growth_info.get('ey_effective_benchmark')  if industry_growth_info else None,
                'eyCapMult':                 industry_growth_info.get('ey_cap_mult')             if industry_growth_info else None,
                'eyCapPct':                  industry_growth_info.get('ey_cap_pct')              if industry_growth_info else None,
                # Shared
                'gdpBase':                   industry_growth_info.get('gdp_base')               if industry_growth_info else None,
                'capped':                    industry_growth_info.get('capped', False)           if industry_growth_info else False,
                'note':                      industry_growth_info.get('note')                    if industry_growth_info else None,
                'earnings_yield_g_note':     industry_growth_info.get('earnings_yield_g_note')  if industry_growth_info else None,
                'damodaranYear': 2026,
                'source':               industry_growth_info.get('source', 'Historical dividends') if industry_growth_info else 'Historical dividends',
                'earningsYieldGrowthSource': industry_growth_info.get('earnings_yield_g_source')   if industry_growth_info else None,
                'usingRegionalData':    industry_growth_info.get('using_regional_data', False)     if industry_growth_info else False,
                'region':               industry_growth_info.get('region')                         if industry_growth_info else None,
            } if industry_growth_info else None,
            'industryName': industry_growth_info.get('industryName') if industry_growth_info else None,
            'autoDetectedIndustry': auto_detected_industry,
            'industrySuggestions': industry_suggestions,
            'tvSector': raw_tv_sector,
            'tvIndustry': raw_tv_industry,
            'growthSource': industry_growth_info.get('source', 'Historical dividends') if industry_growth_info else 'Historical dividends',
            'sources': {
                'beta': source,
                'riskFreeRate': {'US': 'US10Y Treasury (TVC)', 'AU': 'AU10Y Gov Bond (TVC)', 'VN': 'VN10Y Gov Bond (TVC)'}.get(market, 'Gov Bond 10Y'),
                'marketReturn': 'Historical Average',
                'currentPrice': source,
                'dividend': source,
                'dividendGrowth': industry_growth_info.get('source', 'Historical dividends') if industry_growth_info else 'Calculated from History'
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
