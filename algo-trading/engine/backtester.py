"""
runs a strategy over historical data, bar by bar, through the mock
broker. checks stop loss / take profit before it even looks at the
strategy's signal for that row.
"""

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class Backtester:

    def __init__(self, broker, strategy, tracker):
        self.broker = broker
        self.strategy = strategy
        self.tracker = tracker
        self.position = None       # currently open position, or None
        self.equity_curve = []     # [{"Date":, "PortfolioValue":}, ...]
        self.signals_df = None     # stashed so the dashboard can plot it later

    def _close_position(self, exit_date, exit_price, exit_reason, symbol):
        # sells whatever we're holding, works out the pnl, logs the trade
        try:
            quantity = self.position["quantity"]
            entry_price = self.position["entry_price"]
            entry_date = self.position["entry_date"]

            self.broker.place_order(symbol, quantity, "SELL", exit_price, exit_date)

            pnl = (exit_price - entry_price) * quantity

            trade_dict = {
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "side": "BUY",
                "pnl": pnl,
                "exit_reason": exit_reason,
            }
            self.tracker.track_trade(trade_dict)

            if exit_reason == "STOP_LOSS":
                logger.info(f"STOP LOSS triggered: exited at {exit_price} (entry {entry_price})")
            elif exit_reason == "TAKE_PROFIT":
                logger.info(f"TAKE PROFIT triggered: exited at {exit_price} (entry {entry_price})")
            else:
                logger.info(f"SELL signal exit: exited at {exit_price} (entry {entry_price})")

        except Exception as exc:
            logger.error(f"Error closing position: {exc}")
            raise

    def run(self, df, symbol=config.SYMBOL, quantity=config.DEFAULT_QUANTITY):
        # main loop: for every row, check SL/TP first, then check the signal.
        # whatever's left open at the end just stays open, we don't force-close it.
        try:
            self.signals_df = self.strategy.generate_signals(df)
            self.position = None
            self.equity_curve = []

            for _, row in self.signals_df.iterrows():
                date = row["Date"]
                price = row["Close"]

                # risk management comes before the strategy gets a say
                if self.position is not None:
                    entry_price = self.position["entry_price"]
                    stop_loss_price = entry_price * (1 - config.STOP_LOSS_PCT)
                    take_profit_price = entry_price * (1 + config.TAKE_PROFIT_PCT)

                    if price <= stop_loss_price:
                        self._close_position(date, price, "STOP_LOSS", symbol)
                        self.position = None
                    elif price >= take_profit_price:
                        self._close_position(date, price, "TAKE_PROFIT", symbol)
                        self.position = None

                signal = row["Signal"]
                try:
                    if signal == "BUY" and self.position is None:
                        self.broker.place_order(symbol, quantity, "BUY", price, date)
                        self.position = {
                            "entry_date": date,
                            "entry_price": price,
                            "quantity": quantity,
                        }
                    elif signal == "SELL" and self.position is not None:
                        self._close_position(date, price, "SIGNAL", symbol)
                        self.position = None
                    # HOLD, or a BUY/SELL we can't act on right now: nothing to do
                except ValueError as exc:
                    # e.g. broker said no (not enough cash) - log it and keep going
                    logger.error(f"Order skipped on {date}: {exc}")

                self.equity_curve.append({
                    "Date": date,
                    "PortfolioValue": self.broker.get_portfolio_value(price),
                })

            metrics = self.tracker.calculate_metrics()
            logger.info(f"Backtest complete. Final metrics: {metrics}")
            return metrics

        except Exception as exc:
            logger.error(f"Backtest run failed: {exc}")
            raise
