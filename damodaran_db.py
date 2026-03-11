"""
Damodaran Industry Growth Database
SQLite module for managing Damodaran industry growth data.

Updated annually each January from:
https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histgr.html

NOTE (Render deployment): Render's free tier uses an ephemeral filesystem.
The DB is re-seeded from INDUSTRY_DATA_2026 on every cold start, so admin
updates via POST /admin/update-damodaran will persist until the next restart.
To make updates permanent, edit INDUSTRY_DATA_2026 below and redeploy.
"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'damodaran.db')

# ============================================================================
# Seed Data — Damodaran January 2026
# Source: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histgr.html
# Columns: (industry_name, eps_growth_next5yr %, revenue_growth_next5yr %)
# NULL values are stored as None (mapped to SQL NULL)
#
# Worked example (Retail Grocery & Food, USD):
#   eps_growth  = 11.14%
#   benchmark   = 13.95%  (Total Market)
#   gdp_usd     =  3.8%   (current FOMC guidance)
#   weight      = 11.14 / 13.95 = 0.799
#   g           =  3.8% × 0.799 = 3.04%  (displayed as 3.04%)
# ============================================================================

INDUSTRY_DATA_2026 = [
    ("Advertising",                            2.29,   9.22),
    ("Aerospace/Defense",                     25.04,  19.76),
    ("Air Transport",                         30.21,  24.91),
    ("Apparel",                               13.63,   1.64),
    ("Auto & Truck",                          10.22,  10.32),
    ("Auto Parts",                            15.97,   6.03),
    ("Bank (Money Center)",                   13.74,   3.09),
    ("Banks (Regional)",                      13.96,  17.83),
    ("Beverage (Alcoholic)",                   3.89,   0.36),
    ("Beverage (Soft)",                       15.44,   5.04),
    ("Broadcasting",                           0.87,   1.63),
    ("Brokerage & Investment Banking",        20.30,   5.73),
    ("Building Materials",                    10.19,   3.10),
    ("Business & Consumer Services",          12.80,   2.51),
    ("Cable TV",                               5.43,  -0.44),
    ("Chemical (Basic)",                      19.81,  14.97),
    ("Chemical (Diversified)",                 None,   1.71),
    ("Chemical (Specialty)",                   8.46,   7.61),
    ("Coal & Related Energy",                 22.54,  93.17),
    ("Computer Services",                     12.33,  19.46),
    ("Computers/Peripherals",                 25.42,   9.95),
    ("Construction Supplies",                  7.61,  60.81),
    ("Diversified",                            7.57,   2.45),
    ("Drugs (Biotechnology)",                 38.08,  51.48),
    ("Drugs (Pharmaceutical)",                17.81,  33.56),
    ("Education",                             19.03,   4.77),
    ("Electrical Equipment",                  18.86,  27.27),
    ("Electronics (Consumer & Office)",      -56.80,   3.46),
    ("Electronics (General)",                 17.69,  13.82),
    ("Engineering/Construction",              21.04,   6.32),
    ("Entertainment",                          5.75,   7.21),
    ("Environmental & Waste Services",        12.20,  19.88),
    ("Farming/Agriculture",                   11.99,   0.93),
    ("Financial Svcs. (Non-bank & Insurance)", 22.02,  6.38),
    ("Food Processing",                        2.66,   1.87),
    ("Food Wholesalers",                      36.93,   3.04),
    ("Furn/Home Furnishings",                 12.28,   2.35),
    ("Green & Renewable Energy",               7.77,   9.43),
    ("Healthcare Products",                   11.07,  34.66),
    ("Healthcare Support Services",           12.57,   6.22),
    ("Healthcare Information and Technology", 11.17,   7.40),
    ("Homebuilding",                           1.97,   2.27),
    ("Hospitals/Healthcare Facilities",       14.98,   3.82),
    ("Hotel/Gaming",                          13.57,   8.75),
    ("Household Products",                     8.02,   4.29),
    ("Information Services",                  10.12,   2.13),
    ("Insurance (General)",                   24.58,   8.29),
    ("Insurance (Life)",                     -30.45,   3.19),
    ("Insurance (Prop/Cas.)",                 15.33,   5.19),
    ("Investments & Asset Management",        15.00,   6.40),
    ("Machinery",                             13.55,   9.80),
    ("Metals & Mining",                       34.42,  34.44),
    ("Office Equipment & Services",           14.40,   5.28),
    ("Oil/Gas (Integrated)",                   4.14,  -0.26),
    ("Oil/Gas (Production and Exploration)",   4.90,   5.65),
    ("Oil/Gas Distribution",                  12.69,   6.23),
    ("Oilfield Svcs/Equip.",                   3.47,   5.02),
    ("Packaging & Container",                 18.96,   2.24),
    ("Paper/Forest Products",                 -9.30,   1.69),
    ("Power",                                  9.60,   3.78),
    ("Precious Metals",                       71.77,  19.32),
    ("Publishing & Newspapers",                9.39,   3.19),
    ("R.E.I.T.",                               4.29,   3.00),
    ("Real Estate (Development)",             -2.90,   6.30),
    ("Real Estate (General/Diversified)",      None,   None),
    ("Real Estate (Operations & Services)",   33.00,   7.51),
    ("Recreation",                             9.95,   0.63),
    ("Restaurant/Dining",                      3.53,  11.33),
    ("Retail (Automotive)",                   17.82,   2.18),
    ("Retail (Building Supply)",              16.98,   3.16),
    ("Retail (Distributors)",                  9.47,   5.73),
    ("Retail (General)",                      11.71,   4.01),
    ("Retail (Grocery and Food)",             11.14,   3.22),
    ("Retail (REITs)",                         3.99,   4.68),
    ("Retail (Special Lines)",                 8.08,   0.09),
    ("Semiconductor",                         22.88,  11.71),
    ("Semiconductor Equip",                   18.74,   9.97),
    ("Software (Entertainment)",              20.55,   7.78),
    ("Software (Internet)",                   20.90,  17.71),
    ("Software (System & Application)",       22.76,  12.33),
    ("Steel",                                 16.04,   4.93),
    ("Telecom (Wireless)",                    15.10, -20.30),
    ("Telecom. Equipment",                    40.27,  11.68),
    ("Telecom. Services",                     59.42,  20.38),
    ("Transportation",                        15.80,  27.22),
    ("Transportation (Railroads)",             7.66,   3.45),
    ("Trucking",                              20.12,   3.82),
    ("Utility (General)",                      6.91,   2.40),
    ("Utility (Water)",                        7.65,  11.91),
    # Total Market — benchmark denominator (total_market_flag = 1)
    ("Total Market",                          13.95,  15.71),
]

APP_CONFIG_2026 = [
    # GDP growth rates by currency — updated to reflect current guidance (March 2026)
    # USD: 3.8% (FOMC long-run guidance)
    # AUD: 4.0% (RBA potential + inflation target band)
    # VND: 5.5% (Vietnam government target)
    ("gdp_usd",                 "3.8"),
    ("gdp_aud",                 "4.0"),
    ("gdp_vnd",                 "5.5"),
    ("damodaran_source_year",   "2026"),
    ("damodaran_source_url",    "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histgr.html"),
]


# ============================================================================
# Database helpers
# ============================================================================

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed with 2026 data if the DB is empty."""
    conn = _get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS damodaran_growth (
            industry_name           TEXT PRIMARY KEY,
            eps_growth_next5yr      REAL,
            revenue_growth_next5yr  REAL,
            total_market_flag       INTEGER NOT NULL DEFAULT 0,
            source_year             INTEGER NOT NULL DEFAULT 2026,
            last_updated            TEXT    NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS app_config (
            key          TEXT PRIMARY KEY,
            value        TEXT,
            last_updated TEXT NOT NULL
        )
    ''')

    # Seed only if tables are empty
    c.execute('SELECT COUNT(*) FROM damodaran_growth')
    if c.fetchone()[0] == 0:
        today = date.today().isoformat()
        rows = []
        for name, eps, rev in INDUSTRY_DATA_2026:
            is_total = 1 if name == "Total Market" else 0
            rows.append((name, eps, rev, is_total, 2026, today))
        c.executemany(
            'INSERT INTO damodaran_growth '
            '(industry_name, eps_growth_next5yr, revenue_growth_next5yr, '
            ' total_market_flag, source_year, last_updated) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            rows
        )
        print(f"[DB] Seeded {len(rows)} industry rows (Damodaran 2026)")

    c.execute('SELECT COUNT(*) FROM app_config')
    if c.fetchone()[0] == 0:
        today = date.today().isoformat()
        c.executemany(
            'INSERT INTO app_config (key, value, last_updated) VALUES (?, ?, ?)',
            [(k, v, today) for k, v in APP_CONFIG_2026]
        )
        print(f"[DB] Seeded {len(APP_CONFIG_2026)} config entries")

    conn.commit()
    conn.close()


def get_industries():
    """Return all industries A-Z (excludes Total Market row)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT industry_name, eps_growth_next5yr, revenue_growth_next5yr
        FROM   damodaran_growth
        WHERE  total_market_flag = 0
        ORDER  BY industry_name ASC
    ''')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_benchmark():
    """Return the Total Market benchmark row."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT industry_name, eps_growth_next5yr, revenue_growth_next5yr,
               source_year, last_updated
        FROM   damodaran_growth
        WHERE  total_market_flag = 1
    ''')
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_config(key):
    """Return a single config value by key (as string), or None."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM app_config WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else None


# ============================================================================
# Growth rate calculation
# ============================================================================

def calculate_industry_growth(industry_name, currency='USD'):
    """
    Calculate industry-adjusted perpetuity growth rate using Damodaran weighting.

    Algorithm:
      1. GDP base  = gdp_{currency} from app_config
      2. industry_eps  = eps_growth_next5yr for chosen industry
         (fallback: revenue_growth_next5yr if EPS is NULL)
      3. Edge cases:
         - Both NULL  → return GDP base, note: "No data"
         - EPS < 0    → return GDP base, note: "Negative EPS"
         - EPS NULL   → use revenue, note: "Revenue proxy"
      4. weight    = industry_eps / benchmark_eps  (Total Market)
      5. g         = GDP_base × weight
      6. cap at 5% → note: "Capped at 5% perpetuity ceiling"

    Worked example (Retail Grocery & Food, USD, Damodaran 2026):
      eps_growth = 11.14%,  benchmark = 13.95%,  gdp_usd = 3.8%
      weight     = 11.14 / 13.95 = 0.799
      g          = 3.8% × 0.799  = 3.037%  → displayed as 3.04%

    Returns dict:
      g         (float, decimal)  — the growth rate to use
      note      (str | None)      — warning/info message for UI
      capped    (bool)            — whether 5% ceiling was applied
      source    (str)             — human-readable data source label
      weight    (float | None)
      industry_eps_growth  (float | None)
      benchmark_eps_growth (float)
      gdp_base  (float, decimal)
    """
    # Step 1: GDP base
    currency_key = {'USD': 'gdp_usd', 'AUD': 'gdp_aud', 'VND': 'gdp_vnd'}.get(currency, 'gdp_usd')
    gdp_base_pct = float(get_config(currency_key) or '3.8')
    gdp_base = gdp_base_pct / 100

    # Step 2: Fetch industry row
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT eps_growth_next5yr, revenue_growth_next5yr '
        'FROM damodaran_growth WHERE industry_name = ?',
        (industry_name,)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            'g': round(gdp_base, 4),
            'note': f'Industry not found in database — using GDP baseline ({gdp_base_pct}%)',
            'capped': False,
            'source': 'GDP baseline (unknown industry)',
            'weight': None,
            'industry_eps_growth': None,
            'benchmark_eps_growth': None,
            'gdp_base': gdp_base,
        }

    eps_growth = row['eps_growth_next5yr']
    rev_growth = row['revenue_growth_next5yr']

    # Step 3: Edge cases
    note = None
    used_growth = None

    if eps_growth is None and rev_growth is None:
        return {
            'g': round(gdp_base, 4),
            'note': 'No industry growth data available — using GDP baseline',
            'capped': False,
            'source': f'GDP baseline (no data for {industry_name})',
            'weight': None,
            'industry_eps_growth': None,
            'benchmark_eps_growth': None,
            'gdp_base': gdp_base,
        }
    elif eps_growth is None:
        used_growth = rev_growth
        note = 'EPS growth unavailable — using revenue growth as proxy'
    elif eps_growth < 0:
        return {
            'g': round(gdp_base, 4),
            'note': f'Negative industry EPS growth ({eps_growth:.2f}%) not applied — using GDP baseline',
            'capped': False,
            'source': f'GDP baseline (negative EPS for {industry_name})',
            'weight': None,
            'industry_eps_growth': eps_growth,
            'benchmark_eps_growth': None,
            'gdp_base': gdp_base,
        }
    else:
        used_growth = eps_growth

    # Step 4: Weighted calculation
    benchmark = get_benchmark()
    benchmark_eps = benchmark['eps_growth_next5yr'] if benchmark else 13.95
    weight = used_growth / benchmark_eps
    g = gdp_base * weight

    # Step 5: Perpetuity ceiling
    capped = False
    if g > 0.05:
        g = 0.05
        capped = True
        ceiling_note = 'Industry growth capped at 5% perpetuity ceiling'
        note = f'{note}. {ceiling_note}' if note else ceiling_note

    source_year = get_config('damodaran_source_year') or '2026'
    proxy_suffix = ' (revenue proxy)' if (eps_growth is None) else ''
    source = f'Damodaran {source_year} — {industry_name}{proxy_suffix}'

    return {
        'g': round(g, 4),
        'note': note,
        'capped': capped,
        'source': source,
        'weight': round(weight, 4),
        'industry_eps_growth': eps_growth,
        'benchmark_eps_growth': benchmark_eps,
        'gdp_base': gdp_base,
    }


# ============================================================================
# Admin: bulk upsert
# ============================================================================

def update_damodaran_data(source_year, industries):
    """
    Upsert a list of industry rows (used by POST /admin/update-damodaran).
    Also updates damodaran_source_year in app_config.
    Returns count of rows upserted.
    """
    conn = _get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    count = 0

    for ind in industries:
        name = ind.get('industry_name', '').strip()
        if not name:
            continue
        eps = ind.get('eps_growth_next5yr')
        rev = ind.get('revenue_growth_next5yr')
        is_total = 1 if name == 'Total Market' else 0
        c.execute('''
            INSERT INTO damodaran_growth
                (industry_name, eps_growth_next5yr, revenue_growth_next5yr,
                 total_market_flag, source_year, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(industry_name) DO UPDATE SET
                eps_growth_next5yr     = excluded.eps_growth_next5yr,
                revenue_growth_next5yr = excluded.revenue_growth_next5yr,
                total_market_flag      = excluded.total_market_flag,
                source_year            = excluded.source_year,
                last_updated           = excluded.last_updated
        ''', (name, eps, rev, is_total, source_year, today))
        count += 1

    # Update config
    c.execute('''
        INSERT INTO app_config (key, value, last_updated) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value        = excluded.value,
            last_updated = excluded.last_updated
    ''', ('damodaran_source_year', str(source_year), today))

    conn.commit()
    conn.close()
    return count


def get_damodaran_status():
    """Return a summary of the current database state."""
    conn = _get_connection()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) as cnt FROM damodaran_growth WHERE total_market_flag = 0')
    industry_count = c.fetchone()['cnt']

    c.execute('SELECT MAX(last_updated) as lu FROM damodaran_growth')
    last_updated = c.fetchone()['lu']

    conn.close()

    benchmark   = get_benchmark()
    source_year = get_config('damodaran_source_year')
    source_url  = get_config('damodaran_source_url')

    return {
        'source_year':         int(source_year) if source_year else 2026,
        'last_updated':        last_updated,
        'industry_count':      industry_count,
        'benchmark_eps_growth': benchmark['eps_growth_next5yr'] if benchmark else None,
        'source_url':          source_url,
    }
