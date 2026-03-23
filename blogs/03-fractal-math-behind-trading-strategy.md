---
title: "The Math Behind My Trading Bot: Fractals, Hurst Exponents, and Price Action"
tags: python, math, trading, datascience
canonical_url: https://github.com/Godlaw1/godlaws
---

# The Math Behind My Trading Bot: Fractals, Hurst Exponents, and Price Action

No indicators. No machine learning. Just fractal geometry and one statistical test.

This is the math that powers the [Apex Fractal Bot](https://github.com/Godlaw1/godlaws) — an open-source futures trading bot.

## Markets Are Fractal

Benoit Mandelbrot proved in the 1960s that financial markets exhibit fractal behavior. The same patterns that appear on a 1-minute chart appear on a weekly chart. This isn't mysticism — it's a measurable mathematical property.

A fractal market means:
- Price patterns are self-similar across timeframes
- Trends and reversals follow power-law distributions
- The market has "memory" — past price action influences future behavior

## The Hurst Exponent

The Hurst exponent (H) measures whether a time series is trending, random, or mean-reverting:

- **H > 0.5** → Trending (momentum continues)
- **H = 0.5** → Random walk (no predictability)
- **H < 0.5** → Mean-reverting (price snaps back)

Most financial instruments have H values between 0.55 and 0.70 on longer timeframes — they trend. This is the edge.

### Computing H in Python

```python
import numpy as np

def hurst_exponent(prices, max_lag=100):
    """Rescaled range (R/S) analysis."""
    lags = range(2, max_lag)
    tau = []
    for lag in lags:
        chunks = [prices[i:i+lag] for i in range(0, len(prices)-lag, lag)]
        rs_values = []
        for chunk in chunks:
            mean = np.mean(chunk)
            deviations = chunk - mean
            cumulative = np.cumsum(deviations)
            R = max(cumulative) - min(cumulative)
            S = np.std(chunk, ddof=1)
            if S > 0:
                rs_values.append(R / S)
        if rs_values:
            tau.append(np.mean(rs_values))

    log_lags = np.log(list(lags[:len(tau)]))
    log_tau = np.log(tau)
    H = np.polyfit(log_lags, log_tau, 1)[0]
    return H
```

When H > 0.5 and price pulls back to a fractal support level, you have a high-probability trend continuation entry.

## The Fractal Pullback Strategy

1. **Multi-timeframe trend detection** — Confirm the trend on a higher timeframe (daily) before looking for entries on the lower timeframe (1H or 15M)

2. **Fractal level identification** — Mark swing highs and lows using Williams fractals (5-bar pattern). These become support/resistance zones.

3. **Pullback confirmation** — When price retraces to a fractal level, compute the Hurst exponent on recent price data. If H > 0.55, the trend is likely to continue.

4. **Entry and risk management** — Enter at the fractal level with a stop below the previous fractal low. Target the next fractal high or use a trailing stop.

## Why This Works on Futures

Futures markets (ES, NQ, CL, GC) are ideal because:
- High liquidity = minimal slippage
- Nearly 24-hour trading = more opportunities
- Leverage is built in = small accounts can trade meaningfully
- No pattern day trader rules

## Results

The bot has been running live on Apex Trader Funding accounts. The full backtest engine is included in the repo so you can verify everything yourself.

I don't publish equity curves because past performance marketing is exactly the kind of thing this project stands against. Clone the repo, run the backtests, see for yourself.

## Try It Yourself

```bash
git clone https://github.com/Godlaw1/godlaws
cd apex-fractal-bot
pip install -r requirements.txt
python backtest.py --symbol ES --timeframe 1H
```

Everything is open source. Read the code, challenge the math, improve the strategy.

**GitHub:** [github.com/Godlaw1/godlaws](https://github.com/Godlaw1/godlaws)

---

*Godlaws Foundation — open source trading tools for everyone. Founded by Clayd Anthoni.*
