"""
keeps a list of finished trades and crunches the numbers - win rate,
pnl, drawdown, all that.
"""

from utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_TRADE_KEYS = (
    "entry_date", "exit_date", "entry_price", "exit_price",
    "quantity", "side", "pnl", "exit_reason",
)


class PerformanceTracker:

    def __init__(self):
        self.trades = []

    def track_trade(self, trade_dict):
        # just appends to the list, but checks the dict has what we need first
        try:
            missing = [key for key in REQUIRED_TRADE_KEYS if key not in trade_dict]
            if missing:
                raise ValueError(f"trade_dict is missing required keys: {missing}")

            self.trades.append(trade_dict)
            logger.info(
                f"Trade recorded: {trade_dict['side']} qty={trade_dict['quantity']} "
                f"entry={trade_dict['entry_price']} exit={trade_dict['exit_price']} "
                f"pnl={trade_dict['pnl']:.2f} reason={trade_dict['exit_reason']}"
            )
        except ValueError as exc:
            logger.error(f"Failed to track trade: {exc}")
            raise

    def calculate_metrics(self):
        # max_drawdown here is the peak-to-trough dip of cumulative pnl
        # across trades, since we don't have a continuous equity series here
        try:
            if not self.trades:
                logger.info("No trades recorded; returning zeroed metrics.")
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "average_pnl_per_trade": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                    "max_drawdown": 0.0,
                }

            pnls = [trade["pnl"] for trade in self.trades]

            total_trades = len(self.trades)
            winning_trades = sum(1 for pnl in pnls if pnl > 0)
            losing_trades = sum(1 for pnl in pnls if pnl <= 0)
            win_rate = (winning_trades / total_trades) * 100
            total_pnl = sum(pnls)
            average_pnl_per_trade = total_pnl / total_trades
            best_trade = max(pnls)
            worst_trade = min(pnls)

            cumulative = 0.0
            peak = 0.0
            max_drawdown = 0.0
            for pnl in pnls:
                cumulative += pnl
                peak = max(peak, cumulative)
                drawdown = peak - cumulative
                max_drawdown = max(max_drawdown, drawdown)

            metrics = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "average_pnl_per_trade": round(average_pnl_per_trade, 2),
                "best_trade": round(best_trade, 2),
                "worst_trade": round(worst_trade, 2),
                "max_drawdown": round(max_drawdown, 2),
            }

            logger.info(f"Calculated performance metrics: {metrics}")
            return metrics

        except Exception as exc:
            logger.error(f"Error calculating performance metrics: {exc}")
            raise

    def get_trade_history(self):
        return self.trades

    def print_report(self):
        try:
            metrics = self.calculate_metrics()

            print("\n" + "=" * 50)
            print("PERFORMANCE REPORT")
            print("=" * 50)
            print(f"{'Total Trades:':<28}{metrics['total_trades']}")
            print(f"{'Winning Trades:':<28}{metrics['winning_trades']}")
            print(f"{'Losing Trades:':<28}{metrics['losing_trades']}")
            print(f"{'Win Rate:':<28}{metrics['win_rate']:.2f}%")
            print(f"{'Total PnL:':<28}{metrics['total_pnl']:.2f}")
            print(f"{'Average PnL / Trade:':<28}{metrics['average_pnl_per_trade']:.2f}")
            print(f"{'Best Trade:':<28}{metrics['best_trade']:.2f}")
            print(f"{'Worst Trade:':<28}{metrics['worst_trade']:.2f}")
            print(f"{'Max Drawdown:':<28}{metrics['max_drawdown']:.2f}")
            print("=" * 50 + "\n")

        except Exception as exc:
            logger.error(f"Error printing performance report: {exc}")
            raise
