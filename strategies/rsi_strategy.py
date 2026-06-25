"""
RSI strategy, computed by hand (no ta-lib or whatever). buy when it dips
below oversold, sell when it pops above overbought.
"""

import numpy as np
import pandas as pd

import config
from strategies.base_strategy import BaseStrategy
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_rsi(close, period):
    # Wilder's smoothing, the "real" way RSI is supposed to be calculated.
    # seed with a plain average of the first `period` gains/losses, then
    # smooth every value after that recursively.
    try:
        if len(close) <= period:
            raise ValueError(f"Not enough data points ({len(close)}) for RSI period {period}")

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = np.full(len(close), np.nan)
        avg_loss = np.full(len(close), np.nan)

        # delta[0] is always NaN (nothing to diff against), so the seed
        # window is values 1..period
        avg_gain[period] = gain.iloc[1:period + 1].mean()
        avg_loss[period] = loss.iloc[1:period + 1].mean()

        gain_values = gain.values
        loss_values = loss.values

        # can't really vectorize this, each step depends on the last one
        for i in range(period + 1, len(close)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain_values[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss_values[i]) / period

        with np.errstate(divide="ignore", invalid="ignore"):
            rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
            rsi = 100 - (100 / (1 + rs))

        # no losses at all -> RSI is just 100, avoid the divide by zero mess
        rsi = np.where(avg_loss == 0, 100.0, rsi)
        # rows before the seed index don't have a real RSI yet
        rsi = np.where(np.isnan(avg_gain), np.nan, rsi)

        return pd.Series(rsi, index=close.index)

    except Exception as exc:
        logger.error(f"Error calculating RSI: {exc}")
        raise


class RSIStrategy(BaseStrategy):

    def __init__(self, rsi_period=config.RSI_PERIOD,
                 oversold=config.RSI_OVERSOLD, overbought=config.RSI_OVERBOUGHT):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df):
        # adds the RSI column plus Signal, based on threshold crossings
        try:
            if "Close" not in df.columns:
                raise ValueError("DataFrame must contain a 'Close' column")

            result = df.copy()
            result["RSI"] = calculate_rsi(result["Close"], self.rsi_period)

            is_oversold = result["RSI"] < self.oversold
            is_overbought = result["RSI"] > self.overbought

            # fill_value=False keeps these as real bool Series instead of
            # letting shift() inject NaN, which upcasts to object dtype and
            # makes ~ do integer bitwise inversion instead of logical negation
            prev_oversold = is_oversold.shift(1, fill_value=False)
            prev_overbought = is_overbought.shift(1, fill_value=False)

            # wasn't oversold yesterday, is today -> that's the buy trigger
            buy_cross = is_oversold & (~prev_oversold)
            # same idea but for overbought on the other side
            sell_cross = is_overbought & (~prev_overbought)

            result["Signal"] = "HOLD"
            result.loc[buy_cross, "Signal"] = "BUY"
            result.loc[sell_cross, "Signal"] = "SELL"
            result.loc[result["RSI"].isna(), "Signal"] = "HOLD"

            logger.debug(
                f"RSI signals generated: "
                f"{(result['Signal'] == 'BUY').sum()} BUY, "
                f"{(result['Signal'] == 'SELL').sum()} SELL"
            )

            self.validate_signals(result)
            return result

        except Exception as exc:
            logger.error(f"Error generating RSI signals: {exc}")
            raise
