# CAPM & Gordon Model Calculator - Which Version to Use?

## Two Backend Options Available

### Option 1: Claude AI Backend (RECOMMENDED for Accuracy)
**File:** `backend_claude.py`
**Startup:** `START_APP_CLAUDE.bat` or `SETUP_API_KEY.bat`

#### ✅ Advantages:
- **Real-time accurate data** from reliable sources (TradingView, Yahoo Finance, etc.)
- **Actual beta values** specific to each stock (not fixed 1.0)
- **Current risk-free rates** (not hardcoded historical values)
- **Data source transparency** - shows exactly where each metric came from
- **Works for both Vietnamese and US stocks** with proper currency handling
- **Better overall accuracy** - same as the original working version

#### ❌ Disadvantages:
- Requires Anthropic API key (free tier available)
- Slightly slower (2-3 seconds per request due to web search)
- API usage costs (minimal for occasional use)

#### How to Use:
1. Get API key: https://console.anthropic.com/
2. Run `SETUP_API_KEY.bat` and enter your key
3. Or run `START_APP_CLAUDE.bat` and enter key when prompted

---

### Option 2: vnstock/yfinance Backend (FREE but Less Accurate)
**File:** `backend_vnstock.py`
**Startup:** `START_APP.bat`

#### ✅ Advantages:
- **Completely free** - no API key needed
- **Faster** - no web search delay
- **Works offline** (mostly) - uses cached data
- **Good for Vietnamese dividend stocks** with live dividend data

#### ❌ Disadvantages:
- **Fixed beta = 1.0** for all Vietnamese stocks (not accurate)
- **Hardcoded risk-free rates** (3.5% for VN, fetches for US but may be outdated)
- **Limited data sources** - no transparency on where data comes from
- **Less accurate** especially for beta and risk metrics
- **May have rate limiting** issues with Yahoo Finance

#### How to Use:
1. Just run `START_APP.bat`
2. No API key needed

---

## Comparison Table

| Feature | Claude AI Backend | vnstock Backend |
|---------|------------------|-----------------|
| Beta Accuracy | ✅ Real values from TradingView | ❌ Fixed 1.0 for VN stocks |
| Risk-Free Rate | ✅ Current rates | ❌ Hardcoded 3.5% VN |
| Data Sources | ✅ Shown with transparency | ❌ Not shown |
| Cost | 💰 API key required | ✅ Free |
| Speed | ⏱ 2-3 seconds | ✅ <1 second |
| VN Stock Support | ✅ Yes (with multiplier) | ✅ Yes (vnstock) |
| US Stock Support | ✅ Yes (accurate) | ✅ Yes (yfinance) |
| Dividend Data | ✅ Analyst estimates | ✅ Live from vnstock |

---

## Recommendation

### For Most Users: **Claude AI Backend**
The original version you showed me used Claude AI and had much better accuracy. The vnstock backend was created as a workaround when the API key wasn't working, but it sacrifices accuracy for being free.

If you want:
- Accurate beta values
- Current risk-free rates
- Professional-grade analysis
- Data source transparency

→ **Use `START_APP_CLAUDE.bat`**

### For Quick Testing / No API Key: **vnstock Backend**
If you just want to test the app quickly without setting up an API key:

→ **Use `START_APP.bat`**

---

## Setting Up Claude AI Backend

### Step 1: Get API Key
1. Go to https://console.anthropic.com/
2. Sign up (free tier available)
3. Create an API key

### Step 2: Start the App
**Option A - Interactive Setup:**
```
SETUP_API_KEY.bat
```

**Option B - Set Environment Variable:**
```cmd
set ANTHROPIC_API_KEY=your_key_here
START_APP_CLAUDE.bat
```

**Option C - Edit backend_claude.py:**
Open `backend_claude.py` and replace this line:
```python
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
```
with:
```python
ANTHROPIC_API_KEY = 'your_api_key_here'
```

---

## What Fixed in This Update

The vnstock backend had these issues you identified:
1. ❌ Fixed beta (1.0) instead of real beta values
2. ❌ Hardcoded risk-free rate instead of current rates
3. ❌ No data source transparency
4. ❌ Currency display issues (fixed in both versions now)

The Claude AI backend restores the original accuracy while fixing the currency display issues.

---

## Files Summary

- `backend_claude.py` - Accurate backend using Claude AI (RECOMMENDED)
- `backend_vnstock.py` - Free backend using vnstock/yfinance
- `START_APP_CLAUDE.bat` - Start with Claude AI backend
- `START_APP.bat` - Start with vnstock backend
- `SETUP_API_KEY.bat` - Interactive API key setup
- `index.html` - Frontend (works with both backends)

Choose based on your needs: accuracy vs. free/fast.
