# Binance Futures Testnet — Trading Bot

A simple CLI tool for placing orders on Binance Futures Testnet (USDT-M).
Written in Python. No paid APIs needed — runs entirely on testnet with fake money.

**Author:** Siddhik Reddy

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (auth, signing, requests)
│   ├── orders.py          # Order placement logic (market, limit, stop-limit)
│   ├── validators.py      # Input validation before anything hits the network
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # Entry point — CLI via argparse
├── logs/                  # Log files land here (auto-created)
├── .env.example           # Copy this to .env and fill in your keys
├── requirements.txt
└── README.md
```

---

## Setup

**1. Clone and install dependencies**

```bash
git clone <your-repo-url>
cd trading_bot
pip install -r requirements.txt
```

**2. Create a Binance Futures Testnet account**

Go to https://testnet.binancefuture.com and register. It's free — no real money involved.

Under your account, go to **API Management** and generate a key pair.

**3. Set your credentials**

Credentials are stored base64-encoded directly in `cli.py`. Run this once in a Python shell to encode yours:

```python
import base64
print(base64.b64encode(b"your_api_key_here").decode())
print(base64.b64encode(b"your_api_secret_here").decode())
```

Then paste the output into the top of `cli.py`:

```python
_ENC_API_KEY    = b"<your encoded key>"
_ENC_API_SECRET = b"<your encoded secret>"
```

---

## How to Run

### Market Order (BUY)

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Market Order (SELL)

```bash
python cli.py --symbol BTCUSDT --side SELL --type MARKET --quantity 0.01
```

### Limit Order

```bash
python cli.py --symbol ETHUSDT --side BUY --type LIMIT --quantity 0.1 --price 3200
```

### Stop-Limit Order (bonus)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 62000 --stop-price 61500
```

---

## What the Output Looks Like

```
  ─────────────────────────────
   Order Request Summary
  ─────────────────────────────
   Symbol      : BTCUSDT
   Side        : BUY
   Type        : MARKET
   Quantity    : 0.01
  ─────────────────────────────

  ─────────────────────────────
   Order Response
  ─────────────────────────────
   Order ID    : 4152837291
   Symbol      : BTCUSDT
   Side        : BUY
   Type        : MARKET
   Status      : FILLED
   Quantity    : 0.01
   Executed    : 0.01
   Avg Price   : 62345.10
  ─────────────────────────────

  ✓ Order placed successfully.
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log`. Every request, response, and error gets recorded there. The terminal stays quiet unless something actually goes wrong.

Sample log files are included in `logs/` for reference.

---

## Assumptions

- Tested against Binance Futures Testnet only. Do not point this at the live API without reviewing risk limits first.
- Quantity precision varies by symbol. If you get a `LOT_SIZE` error from Binance, adjust your quantity to match the symbol's step size (e.g., 0.001 for BTCUSDT).
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default.
- STOP_LIMIT uses order type `STOP` on the futures API, which maps to a stop-limit execution.
- Credentials are loaded from `.env` using `python-dotenv`. Never commit your `.env` file.
