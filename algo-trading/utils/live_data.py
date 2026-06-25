"""
pulls real OHLC data from yfinance instead of the canned csv. shaped
the same way load_csv() returns data, so nothing downstream needs to
know or care where the data actually came from.
"""

import pandas as pd
import yfinance as yf

from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_live_data(ticker, period="2y", interval="1d"):
    # downloads from yfinance and reshapes to match load_csv()'s output:
    # Date, Open, High, Low, Close, Volume, sorted ascending by date
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)

        if data.empty:
            raise ValueError(f"No data returned for ticker '{ticker}'")

        data = data.reset_index()

        # yfinance sometimes hands back multi-index columns (happens with
        # some ticker/interval combos), flatten that down to plain names
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        # intraday intervals come back with a "Datetime" column instead of "Date"
        date_col = "Datetime" if "Datetime" in data.columns else "Date"
        data = data.rename(columns={date_col: "Date"})

        df = data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)

        # yfinance gives back float32 prices with ugly long tails, round them off
        df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]].round(2)

        logger.info(f"Fetched {len(df)} rows of live data for {ticker}")
        return df

    except Exception as exc:
        logger.error(f"Failed to fetch live data for {ticker}: {exc}")
        raise
