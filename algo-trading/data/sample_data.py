"""
makes up 2 years of fake daily prices for a stock called "DEMO" and
writes it to data/OHLC_data.csv. just a random walk, nothing fancy.

run it directly:
    python data/sample_data.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import get_logger

logger = get_logger(__name__)

START_PRICE = 1000.0
NUM_YEARS = 2
TRADING_DAYS_PER_YEAR = 252
DAILY_VOLATILITY = 0.015  # ~1.5% daily stdev, roughly what a real stock looks like
DAILY_DRIFT = 0.0003       # tiny upward bias so it's not a flat coin flip
RANDOM_SEED = 42           # fixed seed so the data is the same every time we generate it


def generate_ohlc_data(start_price=START_PRICE, num_days=NUM_YEARS * TRADING_DAYS_PER_YEAR):
    # close prices walk randomly day to day, then open/high/low get derived
    # around that close with some extra noise so it looks like a real candle
    try:
        rng = np.random.default_rng(RANDOM_SEED)

        daily_returns = rng.normal(loc=DAILY_DRIFT, scale=DAILY_VOLATILITY, size=num_days)
        close_prices = start_price * np.cumprod(1 + daily_returns)

        # business days only, skips weekends like a real market would
        dates = pd.bdate_range(start=pd.Timestamp.today().normalize() - pd.Timedelta(days=int(num_days * 1.45)),
                                periods=num_days)

        records = []
        prev_close = start_price

        for date, close in zip(dates, close_prices):
            # open gaps a little from yesterday's close
            open_price = prev_close * (1 + rng.normal(0, DAILY_VOLATILITY / 3))

            # high/low just bracket open and close with some randomness
            intraday_range = abs(rng.normal(0, DAILY_VOLATILITY)) * close
            high_price = max(open_price, close) + intraday_range * rng.uniform(0.2, 1.0)
            low_price = min(open_price, close) - intraday_range * rng.uniform(0.2, 1.0)

            # edge case: don't let a wild random draw send price negative
            low_price = max(low_price, 1.0)
            high_price = max(high_price, low_price + 0.01)

            volume = int(rng.uniform(100_000, 1_000_000))

            records.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Open": round(open_price, 2),
                "High": round(high_price, 2),
                "Low": round(low_price, 2),
                "Close": round(close, 2),
                "Volume": volume,
            })

            prev_close = close

        df = pd.DataFrame.from_records(records)
        logger.info(f"Generated {len(df)} rows of synthetic OHLC data for DEMO")
        return df

    except Exception as exc:
        logger.error(f"Failed to generate synthetic OHLC data: {exc}")
        raise


def save_sample_data(output_path=None):
    # generates the data and dumps it to csv, returns where it landed
    try:
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "OHLC_data.csv")

        df = generate_ohlc_data()
        df.to_csv(output_path, index=False)
        logger.info(f"Sample OHLC data saved to {output_path}")
        return output_path

    except Exception as exc:
        logger.error(f"Failed to save sample data: {exc}")
        raise


if __name__ == "__main__":
    saved_path = save_sample_data()
    print(f"Sample data written to: {saved_path}")
