---
title: "I Built an Open-Source Copy Trader That Connects 9 Brokers"
tags: trading, python, api, opensource
canonical_url: https://github.com/Godlaw1/godlaws
---

# I Built an Open-Source Copy Trader That Connects 9 Brokers

One trade signal. Nine brokers. Every account executes simultaneously.

That's what I built, and it's free on GitHub.

## The Problem

If you trade across multiple brokers — and serious traders do — you know the pain:

- You spot an entry on your cTrader account
- You switch to MetaTrader to place the same trade
- You open Alpaca to replicate it there
- By the time you've placed the third trade, the price has moved

Manual replication is slow, error-prone, and costs you money. Commercial copy trading services charge $50-200/month and lock you into their ecosystem.

## The Solution

[Copy Trader](https://github.com/Godlaw1/godlaws) is a self-hosted Python application that:

1. Monitors a master account for new trades
2. Instantly replicates them across all connected broker accounts
3. Manages position sizing relative to each account's balance
4. Handles partial fills, slippage, and broker-specific quirks

### Supported Brokers

| Broker | Protocol | Status |
|--------|----------|--------|
| cTrader | Open API | Active |
| MetaTrader 4/5 | MQL Bridge | Active |
| OANDA | REST API | Active |
| Alpaca | REST API | Active |
| Binance | WebSocket | Active |
| Interactive Brokers | TWS API | Active |
| NinjaTrader | Socket | Active |
| Rithmic | R\|Protocol | Active |
| Coinbase | REST API | Active |

## How It Works

```
Master Account (any broker)
         |
    [Copy Trader Engine]
         |
    +---------+---------+
    |         |         |
 cTrader  Alpaca    OANDA  ... (all connected accounts)
```

The engine runs on any machine — a Raspberry Pi, a VPS, your laptop. It connects to each broker's API, watches for position changes on the master account, and mirrors them everywhere else.

Position sizing is proportional. If your master account is $10,000 and trades 1 lot, a connected $5,000 account trades 0.5 lots automatically.

## Self-Hosted = You Control Everything

No monthly fees. No third party seeing your trades. No vendor lock-in. Your API keys stay on your machine.

Run it with Docker:

```bash
git clone https://github.com/Godlaw1/godlaws
cd copy-trader
cp .env.example .env
# Add your broker credentials
docker-compose up -d
```

## Get Involved

- Star and fork: [github.com/Godlaw1/godlaws](https://github.com/Godlaw1/godlaws)
- Add a broker integration (we'll help you get started)
- Report bugs or suggest features via GitHub Issues

Support the project: [PayPal](https://www.paypal.com/donate?business=ca@godlaws.com&currency_code=EUR) | BTC: `bc1qys4lfrapadd7vwwnqfw4xjs043zxlnetzcp0kt` | SOL: `Ed9eGHW7dfMrYRNYpvxDS7KRoKkfXCDm8Xj5zZ6XBuXH`

---

*Built by Clayd Anthoni at [Godlaws Foundation](https://github.com/Godlaw1/godlaws). Apache 2.0 licensed.*
