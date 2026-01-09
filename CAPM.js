import React, { useState } from 'react';
import { TrendingUp, DollarSign, Info, AlertCircle } from 'lucide-react';

export default function CAPMGordonCalculator() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const calculateValuation = async () => {
    if (!ticker.trim()) {
      setError('Please enter a stock ticker');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      // Call Flask backend API
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/valuation/${ticker.toUpperCase()}`);

      // Check if the API request was successful
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.error || `API error: ${response.status} ${response.statusText}`;
        throw new Error(errorMsg);
      }

      const data = await response.json();

      // Validate required fields
      if (!data.ticker || !data.companyName) {
        throw new Error('Invalid stock data received. Please verify the ticker symbol.');
      }

      setResult(data);

    } catch (err) {
      console.error('Valuation error:', err);

      // Provide more specific error messages
      let errorMessage = err.message;

      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        errorMessage = 'Cannot connect to backend server. Please ensure the Python backend is running on http://localhost:5000';
      } else if (err.message.includes('Invalid ticker')) {
        errorMessage = 'Unable to fetch stock data. Please verify the ticker symbol.';
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-8 h-8 text-indigo-600" />
            <h1 className="text-3xl font-bold text-gray-800">CAPM & Gordon Model Valuation</h1>
          </div>

          <div className="bg-indigo-50 rounded-lg p-4 mb-6 flex gap-3">
            <Info className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-700">
              <p className="font-semibold mb-2">This calculator compares two valuation methods:</p>
              <p className="mb-1"><span className="font-semibold">CAPM:</span> E(R) = Rf + β(Rm - Rf) - Required return based on risk</p>
              <p><span className="font-semibold">Gordon Model:</span> E(R) = (D₁/P₀) + g - Expected return based on dividends</p>
              <p className="text-xs italic">If Gordon return &lt; CAPM return → Stock is OVERVALUED (current price too high, should fall)</p>
              <p className="text-xs italic">If Gordon return &gt; CAPM return → Stock is UNDERVALUED (current price too low, should rise)</p>
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stock Ticker Symbol
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && calculateValuation()}
                placeholder="e.g., AAPL, MSFT, VNM, VCB, FPT"
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-indigo-500 focus:outline-none text-lg font-semibold uppercase"
                disabled={loading}
              />
              <button
                onClick={calculateValuation}
                disabled={loading}
                className="px-8 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              <div className={`rounded-xl p-6 text-white ${
                result.valuation === 'UNDERVALUED' 
                  ? 'bg-gradient-to-r from-green-600 to-emerald-600' 
                  : 'bg-gradient-to-r from-red-600 to-rose-600'
              }`}>
                <h2 className="text-lg font-medium mb-2">{result.companyName}</h2>
                <div className="flex items-center gap-3 mb-2">
                  <AlertCircle className="w-8 h-8" />
                  <div>
                    <p className="text-3xl font-bold">{result.valuation}</p>
                    <p className="text-sm opacity-90">
                      {result.valuation === 'UNDERVALUED' 
                        ? 'Current price < Fair price - Expected to RISE' 
                        : 'Current price > Fair price - Expected to FALL'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-5 border-2 border-blue-200">
                  <h3 className="font-semibold text-gray-800 mb-3">CAPM Analysis</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Required Return:</span>
                      <span className="font-bold text-blue-700">{(result.capmReturn * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-3">
                      <p>Formula: {(result.riskFreeRate * 100).toFixed(2)}% + {result.beta.toFixed(2)} × ({(result.marketReturn * 100).toFixed(2)}% - {(result.riskFreeRate * 100).toFixed(2)}%)</p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 rounded-lg p-5 border-2 border-purple-200">
                  <h3 className="font-semibold text-gray-800 mb-3">Gordon Model Analysis</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Expected Return:</span>
                      <span className="font-bold text-purple-700">{(result.gordonReturn * 100).toFixed(2)}%</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-3">
                      <p>Formula: (${result.dividend.toFixed(2)}/${result.currentPrice.toFixed(2)}) + {(result.dividendGrowth * 100).toFixed(2)}%</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-5">
                <h3 className="font-semibold text-gray-800 mb-3">Valuation Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Current Price</p>
                    <p className="text-2xl font-bold text-gray-800">${result.currentPrice.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Fair Price (CAPM-based)</p>
                    <p className="text-2xl font-bold text-gray-800">${result.fairPrice.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Difference</p>
                    <p className={`text-2xl font-bold ${result.priceDifference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {result.priceDifference > 0 ? '+' : ''}{result.priceDifference.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-5">
                <h3 className="font-semibold text-gray-800 mb-3">Key Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-gray-600">Beta (β)</p>
                    <p className="text-lg font-bold">{result.beta.toFixed(3)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Risk-Free Rate</p>
                    <p className="text-lg font-bold">{(result.riskFreeRate * 100).toFixed(2)}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Annual Dividend</p>
                    <p className="text-lg font-bold">${result.dividend.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Dividend Growth</p>
                    <p className="text-lg font-bold">{(result.dividendGrowth * 100).toFixed(2)}%</p>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 rounded-lg p-5 border border-amber-200">
                <h3 className="font-semibold text-gray-800 mb-3">Interpretation:</h3>
                <p className="text-sm text-gray-700">
                  {result.valuation === 'UNDERVALUED' ? (
                    <>The Gordon Model expected return ({(result.gordonReturn * 100).toFixed(2)}%) is <span className="font-bold text-green-700">higher</span> than the CAPM required return ({(result.capmReturn * 100).toFixed(2)}%). This means the stock is currently <span className="font-bold">undervalued</span> at ${result.currentPrice.toFixed(2)}. The current price is <span className="font-bold text-green-700">below</span> the fair equilibrium price of ${result.fairPrice.toFixed(2)}. You'd expect the stock price to <span className="font-bold text-green-700">rise</span> to reach equilibrium.</>
                  ) : (
                    <>The Gordon Model expected return ({(result.gordonReturn * 100).toFixed(2)}%) is <span className="font-bold text-red-700">lower</span> than the CAPM required return ({(result.capmReturn * 100).toFixed(2)}%). This means the stock is currently <span className="font-bold">overvalued</span> at ${result.currentPrice.toFixed(2)}. The current price is <span className="font-bold text-red-700">above</span> the fair equilibrium price of ${result.fairPrice.toFixed(2)}. You'd expect the stock price to <span className="font-bold text-red-700">fall</span> to reach equilibrium.</>
                  )}
                </p>
              </div>

              {result.sources && (
                <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
                  <h3 className="font-semibold text-gray-700 text-sm mb-3">Data Sources:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-600">
                    <div><span className="font-medium">Beta:</span> {result.sources.beta}</div>
                    <div><span className="font-medium">Risk-Free Rate:</span> {result.sources.riskFreeRate}</div>
                    <div><span className="font-medium">Market Return:</span> {result.sources.marketReturn}</div>
                    <div><span className="font-medium">Current Price:</span> {result.sources.currentPrice}</div>
                    <div><span className="font-medium">Dividend:</span> {result.sources.dividend}</div>
                    <div><span className="font-medium">Dividend Growth:</span> {result.sources.dividendGrowth}</div>
                  </div>
                  <p className="text-xs text-gray-500 mt-3 italic">Powered by Claude AI with real-time web search capabilities</p>
                </div>
              )}

              <p className="text-xs text-gray-500 italic text-center">
                This analysis is based on theoretical models. Actual stock prices may differ due to market sentiment, 
                company-specific events, macroeconomic factors, and other variables not captured by these models. 
                This is not investment advice.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}