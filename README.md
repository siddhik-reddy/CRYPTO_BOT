# Binance Futures Testnet — Trading Bot

A simple CLI tool for placing orders on Binance Futures Testnet (USDT-M).
Written in Python. No paid APIs needed — runs entirely on testnet with fake money.

**Author:** Siddhik Reddy

---

## Project Structure

```
CRYPTO_BOT/
├── cli.py                  # Main CLI interface
├── config.py               # API credentials (gitignored)
├── config.example.py       # Example config template
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── .gitignore             # Git ignore rules
├── bot/                   # Bot module
│   ├── __init__.py
│   ├── client.py          # Binance API client
│   ├── orders.py          # Order placement functions
│   ├── validators.py      # Input validation
│   ├── symbol_info.py     # Symbol rules and limits
│   └── logging_config.py  # Logging configuration
└── logs/                  # Log files directory
    └── bot.log            # Application logs
```

---

## Setup

**1. Clone and install dependencies**

```bash
git clone https://github.com/siddhik-reddy/CRYPTO_BOT.git
cd trading_bot
pip install -r requirements.txt
```

**2. Create a Binance Futures Testnet account**

Go to https://testnet.binancefuture.com and register. It's free — no real money involved.

Under your account, go to **API Management** and generate a key pair.

**3. Set your credentials**

Credentials are stored base64-encoded directly in `cli.py`. Run this once in a Config.py file:

## How to Run


```bash
python cli.py 
```


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


## Assumptions

- Tested against Binance Futures Testnet only. Do not point this at the live API without reviewing risk limits first.
- Quantity precision varies by symbol. If you get a `LOT_SIZE` error from Binance, adjust your quantity to match the symbol's step size (e.g., 0.001 for BTCUSDT).
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default.
- STOP_LIMIT uses order type `STOP` on the futures API, which maps to a stop-limit execution.
- Credentials are loaded from `.env` using `python-dotenv`. Never commit your `.env` file.

```

 Contact
Siddhik Reddy

📧 Email: siddhikreddy440@gmail.com

📱 Phone: +91 8897350151

```
