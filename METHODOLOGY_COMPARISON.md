# CAPM Methodology Comparison

This project includes two versions of the CAPM calculator with different methodologies:

## Version 1: Standard Method (`backend_tradingview.py`)

### CAPM Formula
```
Required Return = Local Risk-Free Rate + β × (Local Market Return - Local Risk-Free Rate)
```

### Parameters by Market

| Market | Risk-Free Rate | Market Return | Source |
|--------|---------------|---------------|--------|
| Vietnam | 4.16% | 9.00% | VN 10Y Gov Bond, VN-Index |
| Australia | 4.20% | 9.50% | AU 10Y Gov Bond, ASX 200 |
| US | Live (~4.2%) | 10.00% | US 10Y Treasury, S&P 500 |

### Pros
- Simple to understand
- Uses local market data
- Familiar to most finance students

### Cons
- Doesn't account for country risk
- May underestimate required returns for emerging markets
- Different risk-free rates make cross-country comparison difficult

---

## Version 2: Damodaran Method (`backend_damodaran.py`)

### CAPM Formula
```
Required Return = US Risk-Free Rate + β × Total Equity Risk Premium
```

Where:
```
Total ERP = Mature Market ERP + Country Risk Premium
```

### Parameters (January 2026 Data)

| Market | Sovereign Rating | Country Risk Premium | Total ERP |
|--------|-----------------|---------------------|-----------|
| Vietnam | Ba2 | 3.90% | **8.13%** |
| Australia | Aaa | 0.00% | **4.23%** |
| US | Aa1 | 0.23% | **4.46%** |

- **Risk-Free Rate**: US 10Y Treasury (used globally) ≈ 4.20%
- **Mature Market ERP**: 4.23% (base premium for Aaa countries)

### Pros
- Accounts for country-specific risk
- Academically rigorous (developed by Prof. Damodaran at NYU Stern)
- Uses consistent global risk-free rate
- Better for emerging market valuations
- Updated regularly (January & July each year)

### Cons
- More complex
- Requires understanding of sovereign credit ratings
- Country risk premiums can change rapidly

---

## Example Comparison

### Vietnamese Stock: VNM (Vinamilk) with β = 0.5

**Standard Method:**
```
Required Return = 4.16% + 0.5 × (9.00% - 4.16%)
               = 4.16% + 0.5 × 4.84%
               = 4.16% + 2.42%
               = 6.58%
```

**Damodaran Method:**
```
Required Return = 4.20% + 0.5 × 8.13%
               = 4.20% + 4.07%
               = 8.27%
```

**Difference: 1.69 percentage points higher with Damodaran method**

This means the Damodaran method requires higher returns to compensate for Vietnam's country risk (Ba2 rating), potentially making more stocks appear undervalued.

---

## Which to Use?

| Scenario | Recommended Method |
|----------|-------------------|
| Academic/classroom exercise | Standard |
| Professional valuation | Damodaran |
| Comparing stocks across countries | Damodaran |
| Quick local market analysis | Standard |
| Emerging market stocks | Damodaran |
| Developed market stocks | Either |

---

## Running Both Versions

### Standard Version (Port 5000)
```bash
python backend_tradingview.py
# OR
START.bat
```

### Damodaran Version (Port 5001)
```bash
python backend_damodaran.py
# OR
START_DAMODARAN.bat
```

Both versions use the same frontend (`index.html`). To switch between backends:
1. Run the desired backend
2. Update `config.js` to point to the correct port

---

## Data Sources

- **Damodaran Data**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html
- **Last Updated**: January 5, 2026
- **Reference Paper**: "Country Risk: Determinants, Measures and Implications - The 2026 Edition"

---

## Updating Damodaran Data

The country risk premiums in `backend_damodaran.py` should be updated twice yearly (January and July) when Prof. Damodaran releases new data.

To update:
1. Visit https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx
2. Find Vietnam, Australia, and US rows
3. Update the `DAMODARAN_COUNTRY_DATA` dictionary in `backend_damodaran.py`
