"""
loads and sanity-checks the OHLC csv before anything else touches it.
"""

import os

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def load_csv(filepath):
    # reads the csv, checks it's not garbage, sorts it, returns a clean df.
    # raises if the file's missing or the columns don't match what we need.
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data file not found: {filepath}")

        df = pd.read_csv(filepath)

        if df.empty:
            raise ValueError(f"Data file is empty: {filepath}")

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns {missing_columns} in {filepath}. "
                f"Expected columns: {REQUIRED_COLUMNS}"
            )

        # dates come in as strings, gotta parse and sort or everything downstream breaks
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)

        # forward-fill small gaps, drop whatever's left over (e.g. leading rows
        # with nothing to fill from)
        price_columns = ["Open", "High", "Low", "Close", "Volume"]
        if df[price_columns].isnull().values.any():
            logger.debug("Missing values detected in OHLC data; forward-filling.")
            df[price_columns] = df[price_columns].ffill()
            df = df.dropna(subset=price_columns).reset_index(drop=True)

        logger.info(f"Loaded {len(df)} rows from {filepath}")
        return df

    except FileNotFoundError as exc:
        logger.error(f"File not found while loading CSV: {exc}")
        raise
    except ValueError as exc:
        logger.error(f"Validation error while loading CSV: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Unexpected error while loading CSV {filepath}: {exc}")
        raise
