---
title: "Why I Open-Sourced My Profitable Trading Bot"
tags: trading, opensource, python, finance
canonical_url: https://github.com/Godlaw1/godlaws
---

# Why I Open-Sourced My Profitable Trading Bot

Most trading bot developers guard their code like it's the nuclear launch codes. I did the opposite — I put mine on GitHub for free.

Here's why.

## The Problem With Trading Software

The retail trading industry has a dirty secret: most of the "trading bots" sold online are garbage. They're over-optimized on historical data, they don't account for slippage or commissions, and the people selling them make more money from sales than from trading.

I spent two years building a fractal pullback strategy that actually works on futures markets. It trades on Apex Trader Funding accounts, uses proper risk management, and has survived real market conditions — not just backtests.

## So Why Give It Away?

Three reasons:

**1. The edge isn't in the code.** My strategy uses fractal geometry and Hurst exponent analysis to identify pullback entries. The logic is maybe 200 lines of Python. The real edge is in execution, risk management, and the discipline to not touch it when it's running. Sharing the code doesn't kill the edge — the futures market has enough liquidity for thousands of traders running similar strategies.

**2. Closed-source trading tools exploit people.** I've seen $5,000 "trading courses" that teach less than a single well-commented Python file. I've seen $200/month bot subscriptions that are just wrappers around basic moving average crossovers. This industry preys on people who want financial freedom but don't know where to start.

**3. Open source makes the code better.** When other traders can read, test, and challenge your strategy, bugs get found faster. Edge cases get handled. New ideas emerge from the community.

## What's in the Repo

The [Godlaws Foundation](https://github.com/Godlaw1/godlaws) maintains two main projects:

- **Apex Fractal Bot** — An automated futures trading bot that uses fractal pullback patterns to enter trends. It includes a full backtesting engine and optimization framework.

- **Copy Trader** — A multi-broker trade replication system that supports 9 brokers: cTrader, MetaTrader, OANDA, Alpaca, Binance, Interactive Brokers, NinjaTrader, and more. One signal, every account gets the trade.

Both are Apache 2.0 licensed. Use them, modify them, build on them.

## The Fractal Strategy in 60 Seconds

Markets aren't random — they're fractal. The same patterns that appear on a 5-minute chart appear on a daily chart. The fractal pullback strategy works like this:

1. Identify the dominant trend using multi-timeframe analysis
2. Wait for a pullback into a fractal support/resistance zone
3. Confirm the pullback is ending using the Hurst exponent (H > 0.5 = trending, H < 0.5 = mean-reverting)
4. Enter with a tight stop and let the trend carry the position

No indicators. No machine learning. Just price action and mathematics.

## How You Can Help

If this resonates with you:

- Star the repo: [github.com/Godlaw1/godlaws](https://github.com/Godlaw1/godlaws)
- Try the bot on a demo account and report what you find
- Contribute a broker integration or strategy improvement
- Share this with someone who's been burned by a $5,000 trading course

If you want to support the infrastructure (servers, market data feeds, API costs), we accept donations via [PayPal](https://www.paypal.com/donate?business=ca@godlaws.com&currency_code=EUR), Bitcoin, and Solana.

## What's Next

We're working on:
- cTrader OAuth integration for the Copy Trader
- A web dashboard for monitoring all connected accounts
- More strategy frameworks beyond fractal pullbacks

The goal is simple: professional-grade trading tools, free and open, for everyone.

---

*Godlaws Foundation is founded by Clayd Anthoni. All code is Apache 2.0 licensed.*

*GitHub: [github.com/Godlaw1/godlaws](https://github.com/Godlaw1/godlaws)*
