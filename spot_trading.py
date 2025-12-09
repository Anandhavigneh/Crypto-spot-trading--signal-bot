import asyncio
import logging
import pandas as pd
import numpy as np
import ccxt.async_support as ccxt
from telegram import Bot
import platform
import json
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Telegram bot token and chat ID
TELEGRAM_TOKEN = "7472779398:AAGykX8czQ8PbXd7eOhMY4nCeJdMigfGZUs"
CHAT_ID = "-4701497456"
# Initialize Binance client
exchange = ccxt.binance({
    'enableRateLimit': True
})

def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

# Function to fetch the selected coins from config
def get_selected_coins():
    config = load_config()
    return config.get("selected_coins", [])


# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)


async def fetch_binance_data(symbol, timeframe="1m", limit=500, max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            # Attempt to fetch the OHLCV data for 1-minute timeframe
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert the data to a Pandas DataFrame
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying {symbol} after {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

    # If all retries fail, log and return an empty DataFrame
    logging.error(f"All {max_retries} attempts failed for {symbol}. Skipping...")
    return pd.DataFrame()

def EMA(close, length, previous_ema):
    alpha = 2 / (length + 1)
    return (close * alpha) + (previous_ema * (1 - alpha))


def calculate_sma(prices, period):
    return prices.rolling(window=period, min_periods=1).mean()


def calculate_ema_with_sma_smoothing(prices, period, smoothing_period):
    ema = prices.copy()
    initial_sma = calculate_sma(prices, smoothing_period)
    ema[:smoothing_period] = initial_sma[:smoothing_period]
    for i in range(smoothing_period, len(prices)):
        ema.iloc[i] = EMA(prices.iloc[i], period, ema.iloc[i - 1])
    return ema


def Supertrend(df, atr_period, multiplier, ema_period1, ema_period2, smoothing_period=9):
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ATR
    price_diffs = [high - low, high - close.shift(), close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean()
    
    # HL2 is the average of high and low prices
    hl2 = (high + low) / 2
    
    # Calculate initial bands
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    
    # Initialize Supertrend column
    supertrend = [True] * len(df)
    direction = [1] * len(df)  # 1 for uptrend, -1 for downtrend
    
    for i in range(1, len(df)):
        if close[i] > final_upperband[i - 1]:
            supertrend[i] = True
            direction[i] = 1
        elif close[i] < final_lowerband[i - 1]:
            supertrend[i] = False
            direction[i] = -1
        else:
            supertrend[i] = supertrend[i - 1]
            direction[i] = direction[i - 1]
            
            # Adjust the bands
            if supertrend[i] and final_lowerband[i] < final_lowerband[i - 1]:
                final_lowerband[i] = final_lowerband[i - 1]
            if not supertrend[i] and final_upperband[i] > final_upperband[i - 1]:
                final_upperband[i] = final_upperband[i - 1]

        # Nullify bands according to trend
        if supertrend[i]:
            final_upperband[i] = np.nan
        else:
            final_lowerband[i] = np.nan
    
    # Calculate EMA using the helper method with SMA(9) for smoothing
    df['EMA1'] = calculate_ema_with_sma_smoothing(close, ema_period1, smoothing_period)
    df['EMA2'] = calculate_ema_with_sma_smoothing(close, ema_period2, smoothing_period)
    
    # Create a single Supertrend Value column
    supertrend_value = pd.Series(final_lowerband)
    supertrend_value[~pd.Series(supertrend)] = final_upperband[~pd.Series(supertrend)]
    
    # Add columns to DataFrame
    df['Supertrend'] = supertrend
    df['Supertrend Direction'] = direction
    df['Supertrend Value'] = supertrend_value
    
    return df


async def check_strategy(df, symbol):
    # Get the most recent values (latest candle)
    prev_supertrend_value = df['Supertrend Value'].iloc[-3]
    prev_ema1 = df['EMA1'].iloc[-3]
    prev_ema2 = df['EMA2'].iloc[-3]
    current_supertrend_value = df['Supertrend Value'].iloc[-2]
    current_ema1 = df['EMA1'].iloc[-2]
    current_ema2 = df['EMA2'].iloc[-2]
    current_open = df['open'].iloc[-1]
    bullish = df['Supertrend'].iloc[-2]

    if prev_supertrend_value < prev_ema1 or prev_supertrend_value < prev_ema2:

        if current_supertrend_value > current_ema1 and current_supertrend_value > current_ema2 and bullish:
            print(f"Entry signal for coin: {symbol}")
            print(f"supertrend:{current_supertrend_value} > Ema1:{current_ema1} and Ema2:{current_ema2}")
            return current_open

    return None


async def send_signal(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info(f"Signal sent: {message}")
    except Exception as e:
        logging.error(f"Error sending signal: {e}")


def get_current_utc_time():
    return datetime.now(timezone.utc).strftime("%H:%M")


def get_current_ist_time():
    # IST is UTC + 5:30
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).strftime("%H:%M")


async def process_symbol(symbol):
    try:
        df = await fetch_binance_data(symbol, timeframe="1m")  # Change timeframe to 1m
        if df.empty:
            logging.warning(f"No data for {symbol}. Skipping...")
            return

        df = Supertrend(df, atr_period=10, multiplier=3, ema_period1=200, ema_period2=365)
        signal = await check_strategy(df, symbol)

        if signal:
            message = f"""
            Trade Signal for {symbol}:

            🔔 Signal Type: Buy Signal  
            💰 Entry Price: {signal}  

            📈 Timeframe: 1-minute  
            ⏰ Signal Generated:  
            - IST Time: {get_current_ist_time()}  
            - UTC Time: {get_current_utc_time()}  
            """
            await send_signal(message)
    except Exception as e:
        logging.error(f"Error processing {symbol}: {e}")
    finally:
        del df


async def wait_for_next_candle():
    """
    Waits until the next 1-minute candle close.
    """
    now = datetime.now(timezone.utc)
    # Calculate the next minute
    next_candle_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Calculate the wait time in seconds
    wait_time = (next_candle_time - now).total_seconds()
    print(f"Waiting {wait_time:.2f} seconds until the next 1-minute candle close at {next_candle_time}...")
    await asyncio.sleep(wait_time)


async def process_symbol_with_semaphore(symbol, semaphore):
    async with semaphore:  # Limit the concurrent execution here
        await process_symbol(symbol)


async def main():
    try:
        selected_coins = get_selected_coins()
        semaphore = asyncio.Semaphore(20)  # Limit the number of concurrent tasks
        while True:
            await wait_for_next_candle()

            tasks = [process_symbol_with_semaphore(symbol, semaphore) for symbol in selected_coins]
            await asyncio.gather(*tasks)  # Gather the tasks to run concurrently
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {e}")
    finally:
        await exchange.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")
    except Exception as e:
        logging.error(f"Error starting main loop: {e}")
