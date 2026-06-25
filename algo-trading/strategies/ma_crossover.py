"""
classic golden cross / death cross strategy. fast MA crosses above slow
MA -> buy, crosses below -> sell.
"""

import config
from strategies.base_strategy import BaseStrategy
from utils.logger import get_logger

logger = get_logger(__name__)


class MovingAverageCrossover(BaseStrategy):

    def __init__(self, fast_period=config.MA_FAST_PERIOD, slow_period=config.MA_SLOW_PERIOD):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, df):
        # bolts MA_Fast/MA_Slow onto the df plus the Signal column the
        # backtester actually cares about
        try:
            if "Close" not in df.columns:
                raise ValueError("DataFrame must contain a 'Close' column")

            result = df.copy()

            result["MA_Fast"] = result["Close"].rolling(window=self.fast_period).mean()
            result["MA_Slow"] = result["Close"].rolling(window=self.slow_period).mean()

            # is fast sitting above slow today?
            fast_above_slow = result["MA_Fast"] > result["MA_Slow"]
            # ...and was it above yesterday? compare the two to catch the
            # exact day the lines cross, not just "fast is above slow".
            # fill_value=False keeps this a real bool Series (shift() without
            # it injects NaN, which upcasts to object dtype and makes ~ do
            # integer bitwise inversion instead of logical negation)
            prev_fast_above_slow = fast_above_slow.shift(1, fill_value=False)

            golden_cross = fast_above_slow & (~prev_fast_above_slow)
            death_cross = (~fast_above_slow) & prev_fast_above_slow

            result["Signal"] = "HOLD"
            result.loc[golden_cross, "Signal"] = "BUY"
            result.loc[death_cross, "Signal"] = "SELL"

            # not enough history yet for the MAs to mean anything, so just hold
            insufficient_history = result["MA_Slow"].isna() | result["MA_Fast"].isna()
            result.loc[insufficient_history, "Signal"] = "HOLD"

            logger.debug(
                f"MA Crossover signals generated: "
                f"{(result['Signal'] == 'BUY').sum()} BUY, "
                f"{(result['Signal'] == 'SELL').sum()} SELL"
            )

            self.validate_signals(result)
            return result

        except Exception as exc:
            logger.error(f"Error generating MA crossover signals: {exc}")
            raise
