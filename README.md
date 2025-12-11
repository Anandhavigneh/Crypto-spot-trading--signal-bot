# Binance Spot Multi-Coin Supertrend Signal

A high-performance crypto market scanner that analyzes multiple Binance Spot trading pairs using Supertrend, EMA-based smoothing, and multi-timeframe confirmation. The bot generates real-time Buy Signals and sends alerts directly to Telegram.

This project is built for traders who need fast, rule-based, automated signal detection across many coins in parallel.

<img width="1230" height="967" alt="Image" src="https://github.com/user-attachments/assets/fec7a278-2b5b-4346-967f-251fe061fe84" />

# Features
## 1. Multi-Coin Scanning System

The bot scans a large list of Binance USDT trading pairs in real time:

Symbol list is defined in config.json

Supports 100+ trading pairs

You can add or remove coins anytime


# config

## 2. 1-Minute Candle Strategy Engine

Each coin uses:

Supertrend indicator

EMA (200 & 365) with SMA-smoothed initialization

ATR-based volatility band calculations

Trend confirmation logic

Reversal & momentum-based entry checks

This ensures signals are generated only during statistically strong bullish reversals.

## 3. Advanced Indicator Framework
Supertrend

The calculation integrates:

ATR-based upper and lower bands

Dynamic band adjustment

Trend direction detection

Band nullification in trend continuation


spot_trading

EMA with SMA Smoothing

EMA initialized using SMA(9) to reduce early-candle noise

Ensures cleaner trend detection

Reduces false entries

EMA periods used:

200 (long-term trend filter)

365 (macro trend filter)

## 4. Robust BUY Signal Logic

A Buy Signal is triggered only when:

Previous Supertrend value < EMA1 or EMA2

Current Supertrend value > both EMAs

Trend direction is bullish

The latest candle confirms upward momentum

Latest open price is used as entry-level

This avoids weak signals and focuses on high-probability setups.

## 5. Telegram Signal Alerts

Every valid signal is sent to your Telegram chat using:

TELEGRAM_TOKEN

CHAT_ID

Message includes:

Symbol

Entry price

Trend confirmation details

IST and UTC timestamps

Telegram integration sourced from:


spot_trading

## 6. High-Speed Async Processing

Async Binance OHLCV fetching

Parallel candle processing using async Semaphores

Handles up to 20+ coins at the same time

Full error handling with retries

This design ensures stability even under rate limits or network instability.

## 7. Automatic 1-Minute Candle Synchronization

The bot:

Detects the next candle close time

Waits precisely until the next minute

Processes all coins only when fresh data is available

This ensures maximum accuracy in signal generation.

Architecture
System Flow
Load config.json → Get selected coins
                      ↓
Wait for next 1-minute candle close
                      ↓
Fetch OHLCV (async)
                      ↓
Apply Supertrend + EMA calculations
                      ↓
Check Buy signal conditions
                      ↓
IF Signal → Send Telegram Alert
                      ↓
Repeat forever

Main Components
config.json

Contains:

Large list of selected trading pairs

Easily editable coin selection list


config

spot_trading.py

Core engine containing:

Binance data fetching

Supertrend logic

EMA smoothing

Signal detection

Telegram messaging

Async task manager


spot_trading

Installation
Requirements
pip install ccxt pandas numpy python-telegram-bot

Edit config.json

Add or remove coins:

"selected_coins": [
  "BTC/USDT",
  "ETH/USDT",
  "BNB/USDT"
]

Add your Telegram bot token and chat ID inside the script:
TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

Running the Bot

Run using Python:

python3 spot_trading.py


## The bot will:

Sync to the next 1-minute candle

Process all configured coins

Send Buy Signals to Telegram

Loop infinitely

Strategy Logic (Detailed)
Supertrend Rules

Uses ATR(10)

Multiplier = 3

Dynamic trend direction

Band switching

Upper/lower band adjustments

EMA + SMA Hybrid System

EMA initialized using SMA(9)

Avoids bad signals early in trend

Smooths out volatility noise

BUY Signal Requirements

Supertrend flipped upward

Trend is bullish

Supertrend > EMA1

Supertrend > EMA2

Confirmation candle validates trend

Entry price = current open price

## Example Output

Telegram message structure:

Trade Signal for BTC/USDT:

Signal Type: Buy Signal
Entry Price: 43000.25

Timeframe: 1-minute
IST Time: 14:05
UTC Time: 08:35

File Structure
|-- spot_trading.py      # Main trading engine
|-- config.json          # Selected coin list
|-- README.md            # Project documentation

## Best Practices

Keep coin list optimized for performance

Use stable internet for real-time scanning

Monitor Telegram alerts regularly

Run the bot on a server for 24/7 uptime

# Disclaimer

This project is for educational and informational purposes only.
No financial returns or trading accuracy are guaranteed.
Using automated trading or signaling tools involves risk.
You are solely responsible for all actions taken using this software.
