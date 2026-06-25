"""
entry point. loads the data, runs both strategies, prints reports,
dumps trade history to csv, then compares them side by side.
"""

import argparse
import os

import pandas as pd

import config
from broker.mock_broker import MockBroker
from engine.backtester import Backtester
from strategies.ma_crossover import MovingAverageCrossover
from strategies.rsi_strategy import RSIStrategy
from tracker.performance import PerformanceTracker
from utils.data_loader import load_csv
from utils.live_data import fetch_live_data
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_args():
    # --live RELIANCE.NS pulls real data via yfinance, otherwise we just
    # use the bundled sample csv
    parser = argparse.ArgumentParser(description="Run the algo trading backtester")
    parser.add_argument("--live", metavar="TICKER",
                         help="Fetch live data for this ticker via yfinance instead of the CSV")
    return parser.parse_args()


def run_strategy_backtest(strategy_name, strategy, df):
    # fresh broker + tracker every time, otherwise strategies would bleed
    # into each other's results
    try:
        logger.info(f"Starting backtest for strategy: {strategy_name}")

        broker = MockBroker(config.INITIAL_BALANCE)
        tracker = PerformanceTracker()
        backtester = Backtester(broker, strategy, tracker)

        metrics = backtester.run(df)

        print(f"\n{'#' * 50}")
        print(f"# STRATEGY: {strategy_name}")
        print(f"{'#' * 50}")
        tracker.print_report()

        return backtester, metrics

    except Exception as exc:
        logger.error(f"Backtest failed for strategy '{strategy_name}': {exc}")
        raise


def save_trade_history(backtester, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        trades = backtester.tracker.get_trade_history()
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(trades)} trades to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to save trade history to {output_path}: {exc}")
        raise


def print_comparison(ma_metrics, rsi_metrics):
    print("\n" + "=" * 70)
    print("STRATEGY COMPARISON: MA Crossover vs RSI")
    print("=" * 70)
    print(f"{'Metric':<28}{'MA Crossover':>20}{'RSI':>20}")
    print("-" * 70)

    rows = [
        ("Total Trades", "total_trades", "{:d}"),
        ("Winning Trades", "winning_trades", "{:d}"),
        ("Losing Trades", "losing_trades", "{:d}"),
        ("Win Rate (%)", "win_rate", "{:.2f}"),
        ("Total PnL", "total_pnl", "{:.2f}"),
        ("Avg PnL / Trade", "average_pnl_per_trade", "{:.2f}"),
        ("Best Trade", "best_trade", "{:.2f}"),
        ("Worst Trade", "worst_trade", "{:.2f}"),
        ("Max Drawdown", "max_drawdown", "{:.2f}"),
    ]

    for label, key, fmt in rows:
        ma_val = fmt.format(ma_metrics[key])
        rsi_val = fmt.format(rsi_metrics[key])
        print(f"{label:<28}{ma_val:>20}{rsi_val:>20}")

    print("=" * 70 + "\n")


def main():
    try:
        logger.info("=== Algo Trading System: Starting main run ===")

        args = parse_args()

        if args.live:
            df = fetch_live_data(args.live)
        else:
            data_path = os.path.join(os.path.dirname(__file__), config.DATA_FILE)
            df = load_csv(data_path)

        ma_strategy = MovingAverageCrossover()
        rsi_strategy = RSIStrategy()

        ma_backtester, ma_metrics = run_strategy_backtest("MA Crossover", ma_strategy, df)
        rsi_backtester, rsi_metrics = run_strategy_backtest("RSI", rsi_strategy, df)

        results_dir = os.path.join(os.path.dirname(__file__), config.RESULTS_DIR)
        os.makedirs(results_dir, exist_ok=True)

        ma_trades_path = os.path.join(os.path.dirname(__file__), config.MA_TRADES_FILE)
        rsi_trades_path = os.path.join(os.path.dirname(__file__), config.RSI_TRADES_FILE)

        save_trade_history(ma_backtester, ma_trades_path)
        save_trade_history(rsi_backtester, rsi_trades_path)

        print_comparison(ma_metrics, rsi_metrics)

        logger.info("=== Algo Trading System: Run complete ===")

    except Exception as exc:
        logger.error(f"Fatal error in main(): {exc}")
        raise


if __name__ == "__main__":
    main()
