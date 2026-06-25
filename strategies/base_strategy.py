"""
every strategy has to inherit from this. keeps the backtester from caring
which strategy it's running, as long as it spits out a Signal column.
"""

from abc import ABC, abstractmethod

from utils.logger import get_logger

logger = get_logger(__name__)

VALID_SIGNALS = ("BUY", "SELL", "HOLD")


class BaseStrategy(ABC):

    @abstractmethod
    def generate_signals(self, df):
        # subclasses fill this in. take the df, slap a Signal column on it,
        # hand it back. nothing else should touch this.
        raise NotImplementedError("Subclasses must implement generate_signals()")

    def validate_signals(self, df):
        # quick gut check so a busted strategy doesn't quietly feed garbage
        # signals into the backtester
        try:
            if "Signal" not in df.columns:
                raise ValueError("DataFrame is missing the 'Signal' column")

            invalid = df.loc[~df["Signal"].isin(VALID_SIGNALS), "Signal"].unique()
            if len(invalid) > 0:
                raise ValueError(f"Invalid signal values found: {invalid}")

            return True
        except ValueError as exc:
            logger.error(f"Signal validation failed: {exc}")
            raise
