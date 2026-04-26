"""
Damodaran Industry Growth Database
SQLite module for managing Damodaran industry growth data.

Two-g design (Option B):
  g               — perpetuity growth (fundgr files, ROE×b)        → used by Gordon DDM
  earnings_yield_g — 5yr EPS forecast (histgr files, analyst view) → used by Earnings Yield

Regional mapping:
  US  → fundgr.xls    / histgr.xls
  AU  → fundgrRest.xls / histgrRest.xls   (Aus/NZ/Canada)
  VN  → fundgremerg.xls / histgremerg.xls (Emerging Markets)

NOTE (Render deployment): Render's free tier uses an ephemeral filesystem.
The DB is re-seeded from INDUSTRY_DATA_2026 on every cold start.
refresh_regional_data() is called at startup to populate damodaran_regional.
"""

import sqlite3
import os
import requests
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'damodaran.db')

# ============================================================================
# Seed Data — Damodaran January 2026
# Source: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histgr.html
# Columns: (industry_name, eps_growth_next5yr %)
# US histgr 5yr analyst EPS forecast — used as legacy fallback when regional
# Excel data hasn't been downloaded yet.
# ============================================================================

INDUSTRY_DATA_2026 = [
    ("Advertising",                             2.29),
    ("Aerospace/Defense",                      25.04),
    ("Air Transport",                          30.21),
    ("Apparel",                                13.63),
    ("Auto & Truck",                           10.22),
    ("Auto Parts",                             15.97),
    ("Bank (Money Center)",                    13.74),
    ("Banks (Regional)",                       13.96),
    ("Beverage (Alcoholic)",                    3.89),
    ("Beverage (Soft)",                        15.44),
    ("Broadcasting",                            0.87),
    ("Brokerage & Investment Banking",         20.30),
    ("Building Materials",                     10.19),
    ("Business & Consumer Services",           12.80),
    ("Cable TV",                                5.43),
    ("Chemical (Basic)",                       19.81),
    ("Chemical (Diversified)",                  None),
    ("Chemical (Specialty)",                    8.46),
    ("Coal & Related Energy",                  22.54),
    ("Computer Services",                      12.33),
    ("Computers/Peripherals",                  25.42),
    ("Construction Supplies",                   7.61),
    ("Diversified",                             7.57),
    ("Drugs (Biotechnology)",                  38.08),
    ("Drugs (Pharmaceutical)",                 17.81),
    ("Education",                              19.03),
    ("Electrical Equipment",                   18.86),
    ("Electronics (Consumer & Office)",       -56.80),
    ("Electronics (General)",                  17.69),
    ("Engineering/Construction",               21.04),
    ("Entertainment",                           5.75),
    ("Environmental & Waste Services",         12.20),
    ("Farming/Agriculture",                    11.99),
    ("Financial Svcs. (Non-bank & Insurance)", 22.02),
    ("Food Processing",                         2.66),
    ("Food Wholesalers",                       36.93),
    ("Furn/Home Furnishings",                  12.28),
    ("Green & Renewable Energy",                7.77),
    ("Healthcare Products",                    11.07),
    ("Healthcare Support Services",            12.57),
    ("Healthcare Information and Technology",  11.17),
    ("Homebuilding",                            1.97),
    ("Hospitals/Healthcare Facilities",        14.98),
    ("Hotel/Gaming",                           13.57),
    ("Household Products",                      8.02),
    ("Information Services",                   10.12),
    ("Insurance (General)",                    24.58),
    ("Insurance (Life)",                      -30.45),
    ("Insurance (Prop/Cas.)",                  15.33),
    ("Investments & Asset Management",         15.00),
    ("Machinery",                              13.55),
    ("Metals & Mining",                        34.42),
    ("Office Equipment & Services",            14.40),
    ("Oil/Gas (Integrated)",                    4.14),
    ("Oil/Gas (Production and Exploration)",    4.90),
    ("Oil/Gas Distribution",                   12.69),
    ("Oilfield Svcs/Equip.",                    3.47),
    ("Packaging & Container",                  18.96),
    ("Paper/Forest Products",                  -9.30),
    ("Power",                                   9.60),
    ("Precious Metals",                        71.77),
    ("Publishing & Newspapers",                 9.39),
    ("R.E.I.T.",                                4.29),
    ("Real Estate (Development)",              -2.90),
    ("Real Estate (General/Diversified)",       None),
    ("Real Estate (Operations & Services)",    33.00),
    ("Recreation",                              9.95),
    ("Restaurant/Dining",                       3.53),
    ("Retail (Automotive)",                    17.82),
    ("Retail (Building Supply)",               16.98),
    ("Retail (Distributors)",                   9.47),
    ("Retail (General)",                       11.71),
    ("Retail (Grocery and Food)",              11.14),
    ("Retail (REITs)",                          3.99),
    ("Retail (Special Lines)",                  8.08),
    ("Semiconductor",                          22.88),
    ("Semiconductor Equip",                    18.74),
    ("Software (Entertainment)",               20.55),
    ("Software (Internet)",                    20.90),
    ("Software (System & Application)",        22.76),
    ("Steel",                                  16.04),
    ("Telecom (Wireless)",                     15.10),
    ("Telecom. Equipment",                     40.27),
    ("Telecom. Services",                      59.42),
    ("Transportation",                         15.80),
    ("Transportation (Railroads)",              7.66),
    ("Trucking",                               20.12),
    ("Utility (General)",                       6.91),
    ("Utility (Water)",                         7.65),
    # Total Market — benchmark denominator (total_market_flag = 1)
    ("Total Market",                           13.95),
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
# Regional Excel URLs  (Damodaran, updated annually each January)
#   fundgr = Fundamental Growth Rate in EPS by Sector (ROE × b)
#   histgr = Historical Growth Rate in EPS by Sector  (5yr analyst EPS forecast)
# ============================================================================

BASE = 'https://pages.stern.nyu.edu/~adamodar/pc/datasets/'

REGIONAL_URLS = {
    'US': {
        'fundamental': BASE + 'fundgr.xls',
        'historical':  BASE + 'histgr.xls',
    },
    'Australia': {
        'fundamental': BASE + 'fundgrRest.xls',
        'historical':  BASE + 'histgrRest.xls',
    },
    'Emerging': {
        'fundamental': BASE + 'fundgremerg.xls',
        'historical':  BASE + 'histgremerg.xls',
    },
}

CURRENCY_TO_REGION = {
    'USD': 'US',
    'AUD': 'Australia',
    'VND': 'Emerging',
}


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
            industry_name      TEXT PRIMARY KEY,
            eps_growth_next5yr REAL,
            total_market_flag  INTEGER NOT NULL DEFAULT 0,
            source_year        INTEGER NOT NULL DEFAULT 2026,
            last_updated       TEXT    NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS app_config (
            key          TEXT PRIMARY KEY,
            value        TEXT,
            last_updated TEXT NOT NULL
        )
    ''')

    # Regional table: fundgr (fundamental g) + histgr (5yr EPS forecast) per region
    c.execute('''
        CREATE TABLE IF NOT EXISTS damodaran_regional (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            region        TEXT    NOT NULL,
            dataset       TEXT    NOT NULL,
            industry_name TEXT    NOT NULL,
            growth_pct    REAL,
            is_benchmark  INTEGER NOT NULL DEFAULT 0,
            source_year   INTEGER NOT NULL DEFAULT 2026,
            last_updated  TEXT    NOT NULL,
            UNIQUE(region, dataset, industry_name)
        )
    ''')

    # Seed damodaran_growth only if empty
    c.execute('SELECT COUNT(*) FROM damodaran_growth')
    if c.fetchone()[0] == 0:
        today = date.today().isoformat()
        rows = []
        for name, eps in INDUSTRY_DATA_2026:
            is_total = 1 if name == "Total Market" else 0
            rows.append((name, eps, is_total, 2026, today))
        c.executemany(
            'INSERT INTO damodaran_growth '
            '(industry_name, eps_growth_next5yr, total_market_flag, source_year, last_updated) '
            'VALUES (?, ?, ?, ?, ?)',
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
        SELECT industry_name, eps_growth_next5yr
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
        SELECT industry_name, eps_growth_next5yr,
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
# Regional data helpers
# ============================================================================

def _get_regional_row(region, dataset, industry_name):
    """Return growth_pct (%) for a specific region/dataset/industry, or None."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT growth_pct FROM damodaran_regional '
        'WHERE region=? AND dataset=? AND industry_name=?',
        (region, dataset, industry_name)
    )
    row = c.fetchone()
    conn.close()
    return row['growth_pct'] if row else None


def _get_regional_benchmark(region, dataset):
    """Return the Total Market benchmark growth_pct (%) for region/dataset, or None."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT growth_pct FROM damodaran_regional '
        'WHERE region=? AND dataset=? AND is_benchmark=1',
        (region, dataset)
    )
    row = c.fetchone()
    conn.close()
    return row['growth_pct'] if (row and row['growth_pct'] is not None) else None


def _apply_g_weight(industry_g_pct, benchmark_pct, gdp_base, gdp_base_pct, industry_name):
    """
    Apply the Damodaran GDP-weighting formula:
        weight = industry_g_pct / benchmark_pct
        g      = gdp_base × weight

    Handles None / negative / outperformance / 2× GDP cap.
    Returns (g: float, note: str|None, capped: bool, weight: float|None).
    """
    if industry_g_pct is None:
        return gdp_base, f'No growth data for {industry_name} — using GDP baseline ({gdp_base_pct:.1f}%)', False, None

    if industry_g_pct < 0:
        note = f'Negative industry growth ({industry_g_pct:.2f}%) — using GDP baseline ({gdp_base_pct:.1f}%)'
        return gdp_base, note, False, None

    if benchmark_pct is None or benchmark_pct <= 0:
        return gdp_base, 'Benchmark unavailable — using GDP baseline', False, None

    weight = industry_g_pct / benchmark_pct
    g = gdp_base * weight

    note = None
    capped = False

    if g > gdp_base:
        note = (f'Industry-adjusted: {g*100:.1f}% '
                f'(above GDP baseline — sector outperformance)')

    if g > 2 * gdp_base:
        g = 2 * gdp_base
        capped = True
        cap_note = f'Capped at 2× GDP baseline ({2*gdp_base_pct:.1f}%)'
        note = f'{note}. {cap_note}' if note else cap_note

    return g, note, capped, weight


# ============================================================================
# Growth rate calculation
# ============================================================================

def calculate_industry_growth(industry_name, currency='USD'):
    """
    Calculate industry-adjusted perpetuity g (Gordon DDM) AND
    earnings-yield g (Earnings Yield signal) using Damodaran weighting.

    Two-g split (Option B):
      g               — from fundgr regional file (ROE×b fundamental growth)
      earnings_yield_g — from histgr regional file (5yr analyst EPS forecast)

    Both use the same GDP-weighting formula:
      weight = industry_g / benchmark_g
      g_final = gdp_base × weight        (capped at 2× gdp_base)

    Falls back to legacy damodaran_growth table (US histgr seed data) when
    regional Excel data hasn't been downloaded yet.

    Returns dict with keys:
      g                     — perpetuity growth rate (decimal) for Gordon DDM
      earnings_yield_g      — 5yr EPS growth rate (decimal) for Earnings Yield
      note                  — warning/info for perpetuity g
      earnings_yield_g_note — warning/info for EY g
      capped                — whether 2× ceiling was applied to g
      source                — human-readable label for g
      earnings_yield_g_source — human-readable label for EY g
      weight                — Damodaran weight used for g
      industry_eps_growth   — raw industry fundgr % (or legacy histgr %)
      benchmark_eps_growth  — raw benchmark %
      industry_hist_growth  — raw histgr % (None if not available)
      benchmark_hist_growth — raw histgr benchmark % (None if not available)
      gdp_base              — GDP base rate (decimal)
      region                — 'US' / 'Australia' / 'Emerging'
      using_regional_data   — True if live Excel data was used
    """
    # ── Step 1: GDP base ─────────────────────────────────────────────────────
    currency_key = {'USD': 'gdp_usd', 'AUD': 'gdp_aud', 'VND': 'gdp_vnd'}.get(currency, 'gdp_usd')
    gdp_base_pct = float(get_config(currency_key) or '3.8')
    gdp_base = gdp_base_pct / 100

    region = CURRENCY_TO_REGION.get(currency, 'US')
    source_year = get_config('damodaran_source_year') or '2026'

    # ── Step 2: Try regional data (fundgr + histgr) ───────────────────────────
    fund_g_pct  = _get_regional_row(region, 'fundamental', industry_name)
    fund_bm_pct = _get_regional_benchmark(region, 'fundamental')
    hist_g_pct  = _get_regional_row(region, 'historical', industry_name)
    hist_bm_pct = _get_regional_benchmark(region, 'historical')

    using_regional = (
        fund_g_pct is not None
        and fund_bm_pct is not None
        and fund_bm_pct > 0
    )

    if using_regional:
        # ── Regional path ────────────────────────────────────────────────────
        g, g_note, g_capped, g_weight = _apply_g_weight(
            fund_g_pct, fund_bm_pct, gdp_base, gdp_base_pct, industry_name)

        hist_data_ok = (hist_g_pct is not None
                        and hist_bm_pct is not None
                        and hist_bm_pct > 0)

        if hist_data_ok:
            g_ey, g_ey_note, _, g_ey_weight = _apply_g_weight(
                hist_g_pct, hist_bm_pct, gdp_base, gdp_base_pct, industry_name)
            g_ey_source = (f'Damodaran {source_year} {region} — '
                           f'{industry_name} (5yr EPS forecast)')
        else:
            g_ey        = g
            g_ey_note   = 'Historical EPS data unavailable — using fundamental growth'
            g_ey_weight = g_weight
            g_ey_source = (f'Damodaran {source_year} {region} — '
                           f'{industry_name} (fundamental, EPS n/a)')

        return {
            'g':                      round(g, 4),
            'earnings_yield_g':       round(g_ey, 4),
            'note':                   g_note,
            'earnings_yield_g_note':  g_ey_note,
            'capped':                 g_capped,
            'source':                 (f'Damodaran {source_year} {region} — '
                                       f'{industry_name} (fundamental)'),
            'earnings_yield_g_source': g_ey_source,
            # Gordon DDM computation inputs (fundgr)
            'weight':                 round(g_weight, 4) if g_weight is not None else None,
            'industry_eps_growth':    fund_g_pct,
            'benchmark_eps_growth':   fund_bm_pct,
            # Earnings Yield computation inputs (histgr)
            'earnings_yield_weight':  round(g_ey_weight, 4) if g_ey_weight is not None else None,
            'industry_hist_growth':   hist_g_pct,
            'benchmark_hist_growth':  hist_bm_pct,
            'gdp_base':               gdp_base,
            'region':                 region,
            'using_regional_data':    True,
        }

    # ── Legacy path: damodaran_growth table (US histgr seed data) ────────────
    # Used when regional Excel files haven't been downloaded yet.
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        'SELECT eps_growth_next5yr FROM damodaran_growth WHERE industry_name = ?',
        (industry_name,)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            'g':                      round(gdp_base, 4),
            'earnings_yield_g':       round(gdp_base, 4),
            'note':                   f'Industry not found — using GDP baseline ({gdp_base_pct}%)',
            'earnings_yield_g_note':  None,
            'capped':                 False,
            'source':                 'GDP baseline (unknown industry)',
            'earnings_yield_g_source': 'GDP baseline (unknown industry)',
            'weight':                 None,
            'industry_eps_growth':    None,
            'benchmark_eps_growth':   None,
            'industry_hist_growth':   None,
            'benchmark_hist_growth':  None,
            'gdp_base':               gdp_base,
            'region':                 region,
            'using_regional_data':    False,
        }

    eps_growth = row['eps_growth_next5yr']

    # Edge-case: NULL or negative EPS → fall back to GDP baseline
    if eps_growth is None:
        return {
            'g':                      round(gdp_base, 4),
            'earnings_yield_g':       round(gdp_base, 4),
            'note':                   f'No EPS growth data for {industry_name} — using GDP baseline',
            'earnings_yield_g_note':  None,
            'capped':                 False,
            'source':                 f'GDP baseline (no data for {industry_name})',
            'earnings_yield_g_source': f'GDP baseline (no data for {industry_name})',
            'weight':                 None,
            'industry_eps_growth':    None,
            'benchmark_eps_growth':   None,
            'industry_hist_growth':   None,
            'benchmark_hist_growth':  None,
            'gdp_base':               gdp_base,
            'region':                 region,
            'using_regional_data':    False,
        }

    if eps_growth < 0:
        return {
            'g':                      round(gdp_base, 4),
            'earnings_yield_g':       round(gdp_base, 4),
            'note':                   f'Negative EPS growth ({eps_growth:.2f}%) — using GDP baseline',
            'earnings_yield_g_note':  None,
            'capped':                 False,
            'source':                 f'GDP baseline (negative EPS for {industry_name})',
            'earnings_yield_g_source': f'GDP baseline (negative EPS for {industry_name})',
            'weight':                 None,
            'industry_eps_growth':    eps_growth,
            'benchmark_eps_growth':   None,
            'industry_hist_growth':   None,
            'benchmark_hist_growth':  None,
            'gdp_base':               gdp_base,
            'region':                 region,
            'using_regional_data':    False,
        }

    benchmark = get_benchmark()
    benchmark_eps = benchmark['eps_growth_next5yr'] if benchmark else 13.95
    g, g_note, g_capped, g_weight = _apply_g_weight(
        eps_growth, benchmark_eps, gdp_base, gdp_base_pct, industry_name)

    source_label = f'Damodaran {source_year} — {industry_name} (legacy US histgr)'

    return {
        'g':                      round(g, 4),
        'earnings_yield_g':       round(g, 4),   # same as g in legacy path
        'note':                   g_note,
        'earnings_yield_g_note':  None,
        'capped':                 g_capped,
        'source':                 source_label,
        'earnings_yield_g_source': source_label,
        'weight':                 round(g_weight, 4) if g_weight is not None else None,
        'industry_eps_growth':    eps_growth,
        'benchmark_eps_growth':   benchmark_eps,
        'industry_hist_growth':   None,
        'benchmark_hist_growth':  None,
        'gdp_base':               gdp_base,
        'region':                 region,
        'using_regional_data':    False,
    }


# ============================================================================
# Admin: bulk upsert (legacy manual update endpoint)
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
        is_total = 1 if name == 'Total Market' else 0
        c.execute('''
            INSERT INTO damodaran_growth
                (industry_name, eps_growth_next5yr, total_market_flag,
                 source_year, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(industry_name) DO UPDATE SET
                eps_growth_next5yr = excluded.eps_growth_next5yr,
                total_market_flag  = excluded.total_market_flag,
                source_year        = excluded.source_year,
                last_updated       = excluded.last_updated
        ''', (name, eps, is_total, source_year, today))
        count += 1

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

    # Regional table stats
    c.execute('''
        SELECT region, dataset, COUNT(*) as cnt, MAX(last_updated) as lu
        FROM damodaran_regional
        GROUP BY region, dataset
    ''')
    regional_rows = [dict(r) for r in c.fetchall()]

    conn.close()

    benchmark   = get_benchmark()
    source_year = get_config('damodaran_source_year')
    source_url  = get_config('damodaran_source_url')

    return {
        'source_year':          int(source_year) if source_year else 2026,
        'last_updated':         last_updated,
        'industry_count':       industry_count,
        'benchmark_eps_growth': benchmark['eps_growth_next5yr'] if benchmark else None,
        'source_url':           source_url,
        'regional_datasets':    regional_rows,
    }


# ============================================================================
# Regional Excel refresh  (Option B)
# ============================================================================

def fetch_damodaran_excel(url, dataset_type):
    """
    Download and parse a Damodaran .xls growth-rate file using xlrd.

    dataset_type:
      'fundamental' — fundgr files: ROE×b column ("Expected Growth in EPS",
                      current-ROE variant, col ~6)
      'historical'  — histgr files: "Expected Growth in EPS - Next 5 years"
                      column (col ~6)

    Both file families use the same column-6 position for the primary metric.
    Header detection is attempted first; positional col-6 is the fallback.

    Returns list of (industry_name: str, growth_pct: float|None).
    Returns empty list on any failure.
    """
    try:
        import xlrd
    except ImportError:
        print('[DAMODARAN] xlrd not installed — run: pip install xlrd==1.2.0')
        return []

    filename = url.split('/')[-1]

    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
    except Exception as e:
        print(f'[DAMODARAN] HTTP error fetching {filename}: {e}')
        return []

    try:
        wb = xlrd.open_workbook(file_contents=resp.content)
    except Exception as e:
        print(f'[DAMODARAN] xlrd could not open {filename}: {e}')
        return []

    ws = wb.sheets()[0]
    if ws.nrows < 3 or ws.ncols < 2:
        print(f'[DAMODARAN] Unexpected sheet dimensions {ws.nrows}×{ws.ncols}: {filename}')
        return []

    # ── Locate header row (first row where col-0 contains "industry") ─────────
    header_row = None
    for i in range(min(5, ws.nrows)):
        cell = str(ws.cell_value(i, 0)).lower()
        if 'industry' in cell:
            header_row = i
            break
    if header_row is None:
        header_row = 1   # Damodaran: row-0 = title, row-1 = headers

    headers = [str(ws.cell_value(header_row, j)).lower().strip()
               for j in range(ws.ncols)]
    print(f'[DAMODARAN] {filename} headers[{header_row}]: {headers}')

    # ── Locate target column ─────────────────────────────────────────────────
    target_col = None

    if dataset_type == 'historical':
        # histgr: "Expected Growth in EPS - Next 5 years"
        for j, h in enumerate(headers):
            if 'expected' in h and ('5' in h or 'next' in h or 'forecast' in h):
                target_col = j
                break

    else:  # 'fundamental'
        # fundgr: "Expected Growth in EPS" via current ROE×retention.
        # The file also has a "non-cash" / "stable" variant — skip those.
        skip = {'stable', 'non-cash', 'noncash', 'net income'}
        for j, h in enumerate(headers):
            if ('expected' in h and 'growth' in h
                    and not any(s in h for s in skip)):
                target_col = j
                break

    if target_col is None:
        target_col = 6   # positional fallback (both fundgr and histgr use col 6)
    if target_col >= ws.ncols:
        target_col = ws.ncols - 1

    col_label = headers[target_col] if target_col < len(headers) else '?'
    print(f'[DAMODARAN] {filename} dataset={dataset_type} → col {target_col} = "{col_label}"')

    # ── Parse data rows ───────────────────────────────────────────────────────
    SKIP_PHRASES = {
        'weighted average', 'simple average', 'note:', 'source:', 'data:',
        'aggregated across', 'total market (with',
    }

    results = []
    for i in range(header_row + 1, ws.nrows):
        raw_name = ws.cell_value(i, 0)
        if raw_name == '' or raw_name is None:
            continue
        name = str(raw_name).strip()
        if not name:
            continue
        if any(p in name.lower() for p in SKIP_PHRASES):
            continue

        try:
            raw = ws.cell_value(i, target_col)
            if raw == '' or raw is None:
                growth_pct = None
            else:
                growth_pct = float(raw)
                # Sanity check: Damodaran always stores % (e.g. 11.14 not 0.1114).
                # If somehow all values look like decimal (all < 1.5), convert.
                # We defer this check to after we collect all rows (see below).
        except (ValueError, TypeError):
            growth_pct = None

        results.append((name, growth_pct))

    # ── Decimal-vs-percent auto-detection ────────────────────────────────────
    # Damodaran uses % format. Sanity-check the Total Market row.
    # If its value looks like 0.14 instead of 14.0, multiply all by 100.
    numeric = [g for _, g in results if g is not None]
    if numeric and max(abs(v) for v in numeric) < 2.0:
        print(f'[DAMODARAN] {filename} values appear to be decimal — converting to %')
        results = [(n, g * 100 if g is not None else None) for n, g in results]

    print(f'[DAMODARAN] Parsed {len(results)} rows from {filename}')
    return results


def refresh_regional_data():
    """
    Download all 6 Damodaran regional Excel files and upsert into
    damodaran_regional table.

    Called at startup (best-effort, in background thread) and by the
    admin /api/admin/refresh-damodaran endpoint.

    Returns dict: { region: { dataset: { 'status': 'ok'|'error', 'count': N } } }
    """
    report = {}
    conn = _get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    source_year = int(get_config('damodaran_source_year') or 2026)

    for region, datasets in REGIONAL_URLS.items():
        report[region] = {}
        for dataset_type, url in datasets.items():
            rows = fetch_damodaran_excel(url, dataset_type)
            if not rows:
                report[region][dataset_type] = {'status': 'error', 'count': 0}
                print(f'[DAMODARAN] No data for region={region} dataset={dataset_type}')
                continue

            count = 0
            for name, growth_pct in rows:
                is_benchmark = 1 if name.strip() == 'Total Market' else 0
                try:
                    c.execute('''
                        INSERT INTO damodaran_regional
                            (region, dataset, industry_name, growth_pct,
                             is_benchmark, source_year, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(region, dataset, industry_name) DO UPDATE SET
                            growth_pct   = excluded.growth_pct,
                            is_benchmark = excluded.is_benchmark,
                            source_year  = excluded.source_year,
                            last_updated = excluded.last_updated
                    ''', (region, dataset_type, name, growth_pct,
                          is_benchmark, source_year, today))
                    count += 1
                except Exception as e:
                    print(f'[DAMODARAN] DB upsert error for {name!r}: {e}')

            conn.commit()
            report[region][dataset_type] = {'status': 'ok', 'count': count}
            print(f'[DAMODARAN] Stored {count} rows '
                  f'(region={region}, dataset={dataset_type})')

    conn.close()
    return report
