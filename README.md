# CAPM & Gordon Model Stock Valuation Calculator

A comprehensive stock valuation tool that combines the Capital Asset Pricing Model (CAPM) and Gordon Growth Model to analyze both Vietnamese and US stocks.

## Features

- **Dual Market Support**: Analyze both Vietnamese (VN30+) and US stocks with market selector
- **CAPM Analysis**: Calculate required return based on systematic risk (beta)
- **Gordon Growth Model**: Estimate fair value using dividend discount model with D₁ formula
- **P/E Ratio Analysis**: Compare actual vs theoretical P/E ratios with detailed breakdown
- **Smart Warnings**:
  - High-growth stock detection (when g > ke)
  - Irregular dividend pattern detection for US stocks
  - Low dividend warnings
- **Real-Time Data**:
  - Live US Treasury rates via yfinance
  - TradingView scraping for accurate beta and price data
  - Vietnamese stock data from VCI via vnstock
- **Educational**: Complete assumptions and limitations documentation

## Architecture

- **Frontend**: React (vanilla CDN setup) with Tailwind CSS
- **Backend**: Python Flask with TradingView web scraping
- **Data Sources**:
  - TradingView for beta and real-time prices
  - Yahoo Finance for US stock fundamentals and Treasury rates
  - vnstock for Vietnamese stock data (VCI source)
  - Alpha Vantage for US stock P/E ratios (optional)

## Installation

### 1. Install Python Dependencies

```bash
pip install flask flask-cors requests beautifulsoup4 yfinance vnstock pandas numpy
```

Required packages:
- `flask` - Web framework
- `flask-cors` - CORS handling
- `requests` - HTTP requests for TradingView scraping
- `beautifulsoup4` - HTML parsing for web scraping
- `yfinance` - Yahoo Finance data (US stocks)
- `vnstock` - Vietnamese stock data (VCI source)
- `pandas` - Data manipulation
- `numpy` - Numerical calculations

### 2. Start the Backend Server

```bash
python backend_tradingview.py
```

The Flask server will start on `http://localhost:5000`

### 3. Open the Frontend

Simply open `index.html` in your browser:
- **Option 1**: Double-click `index.html`
- **Option 2**: Right-click → Open with → Your browser
- **Option 3**: Use a local server:
  ```bash
  python -m http.server 8000
  # Then visit http://localhost:8000
  ```

No build tools or npm required! The frontend uses React via CDN.

## How It Works

1. **User selects market** (Vietnam or US) using flag buttons
2. **User enters a stock ticker** (e.g., VNM, AAPL)
3. **React frontend calls Flask API**: `http://localhost:5000/api/valuation/{ticker}?market={VN|US}`
4. **Backend fetches real-time data**:
   - **Beta & Price**: TradingView web scraping
   - **US Stocks**: yfinance for dividends, Treasury rates, fundamentals
   - **VN Stocks**: vnstock for P/E ratios, fundamentals from VCI
5. **Backend calculates**:
   - **CAPM Return**: `E(R) = Rf + β(Rm - Rf)`
   - **Gordon Return**: `E(R) = (D₁/P₀) + g` where `D₁ = D₀ × (1 + g)`
   - **Fair Price**: `P = D₁ / (ke - g)`
   - **Theoretical P/E**: `P/E = Payout Ratio / (ke - g)`
6. **Determines valuation**:
   - If Gordon Return > CAPM Return → **UNDERVALUED** (price should rise)
   - If Gordon Return < CAPM Return → **OVERVALUED** (price should fall)
7. **Displays warnings** if applicable:
   - High-growth stocks (g > ke)
   - Irregular dividend patterns
   - Low dividend yields

## API Endpoints

### GET `/api/valuation/<ticker>`
Calculates CAPM and Gordon Model valuation for a stock.

**Example Request:**
```bash
curl http://localhost:5000/api/valuation/AAPL
```

**Example Response:**
```json
{
  "ticker": "AAPL",
  "companyName": "Apple Inc.",
  "beta": 1.286,
  "riskFreeRate": 0.0445,
  "marketReturn": 0.1123,
  "currentPrice": 185.50,
  "dividend": 0.96,
  "dividendGrowth": 0.0612,
  "capmReturn": 0.1317,
  "gordonReturn": 0.0664,
  "fairPrice": 13.64,
  "valuation": "OVERVALUED",
  "priceDifference": -92.65,
  "sources": {
    "beta": "Yahoo Finance",
    "riskFreeRate": "US 10-Year Treasury (^TNX)",
    "marketReturn": "S&P 500 10-year historical return",
    "currentPrice": "Yahoo Finance Real-time",
    "dividend": "Yahoo Finance Dividend Data",
    "dividendGrowth": "Calculated from historical dividends"
  }
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "CAPM & Gordon Model API is running"
}
```

## Valuation Logic

The calculator compares two different approaches:

### CAPM (Capital Asset Pricing Model)
- Calculates the **required return** based on systematic risk
- Formula: `E(R) = Rf + β(Rm - Rf)`
- Where:
  - `Rf` = Risk-free rate (10-year Treasury)
  - `β` = Beta (stock's sensitivity to market)
  - `Rm` = Market return (S&P 500 average)

### Gordon Growth Model
- Calculates the **expected return** based on dividends
- Formula: `E(R) = (D1/P0) + g`
- Where:
  - `D1` = Next year's expected dividend
  - `P0` = Current stock price
  - `g` = Dividend growth rate

### Fair Price Calculation
- Uses Gordon Growth Model: `Fair Price = D1 / (r - g)`
- Where `r` is the CAPM required return

### Interpretation
- **UNDERVALUED**: Gordon return > CAPM return
  - Current price < Fair price
  - Stock expected to RISE
- **OVERVALUED**: Gordon return < CAPM return
  - Current price > Fair price
  - Stock expected to FALL

## Project Structure

```
CAPM, gordon valuation coding/
├── backend.py           # Flask API server
├── CAPM.js             # React frontend component
├── requirements.txt    # Python dependencies
├── .env.example        # (Legacy - not needed anymore)
└── README.md           # This file
```

## Supported Vietnamese Stocks

All **VN30 Index** stocks are fully supported:
- **Banking**: VCB, BID, CTG, TCB, MBB, VPB, ACB, HDB, TPB, STB, SHB, VIB, LPB, SSB
- **Real Estate**: VIC, VHM, VRE, DGC
- **Industrial**: HPG, GVR
- **Energy**: GAS, PLX
- **Consumer**: VNM, MSN, MWG, SAB
- **Technology**: FPT
- **Securities**: SSI
- **Transportation**: VJC
- **Construction**: BCM

Plus **60+ additional Vietnamese stocks** across all sectors including securities, insurance, retail, transportation, and more.

## Supported US Stocks

Works with most US stocks on Yahoo Finance and TradingView:
- Large caps: AAPL, MSFT, GOOGL, TSLA, etc.
- Dividend stocks: KO, JNJ, PG, etc.
- Growth stocks: NVDA, META, AMZN (with warnings for irregular dividends)

**Note**: Best suited for dividend-paying stocks. Growth stocks with no/irregular dividends will show warnings.

## Troubleshooting

### "Cannot connect to backend server"
- Make sure Python backend is running: `python backend.py`
- Check that it's running on `http://localhost:5000`
- Check firewall settings

### "Invalid ticker symbol"
- Verify the ticker exists on Yahoo Finance
- Try the ticker on https://finance.yahoo.com first
- Some international tickers may not work

### Backend crashes or errors
- Make sure all Python dependencies are installed
- Check Python version (requires Python 3.7+)
- Look at console output for specific error messages

## Model Assumptions & Limitations

### CAPM Assumptions
- Investors hold diversified portfolios to eliminate unsystematic risk
- Single-period transaction horizon
- Investors can borrow and lend at the risk-free rate
- Perfect capital market (no transaction costs, taxes, or restrictions)
- All investors have homogeneous expectations

### Gordon Growth Model Assumptions
- Company exists forever (perpetuity)
- Dividends increase at a constant rate indefinitely
- Required rate of return (ke) must be greater than growth rate (g)
- Stable economic environment

### Key Limitations
- **CAPM**: Assumes market efficiency; ignores transaction costs (rarely holds in reality)
- **Gordon Model**: Assumes constant dividend growth (rare due to business cycles)
- **Gordon Model**: Not suitable for high-growth or non-dividend-paying stocks
- **Both models**: Don't capture market sentiment, company events, or macro shocks

For detailed documentation, see the "Model Assumptions & Limitations" section in the calculator interface.

**Sources**: [Investopedia CAPM](https://www.investopedia.com/terms/c/capm.asp) | [Investopedia Gordon Model](https://www.investopedia.com/terms/g/gordongrowthmodel.asp)

## Disclaimer

This tool is for educational purposes only. The analysis is based on theoretical financial models, and actual stock prices may differ significantly due to market sentiment, company-specific events, macroeconomic factors, and other variables not captured by these models.

**This is not investment advice.** Always conduct your own thorough research and consult with financial professionals before making investment decisions.
