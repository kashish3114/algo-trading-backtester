"""
tests for the backtester - stop loss, take profit, and a full run.
"""

import pandas as pd

import config
from broker.mock_broker import MockBroker
from engine.backtester import Backtester
from strategies.base_strategy import BaseStrategy
from strategies.ma_crossover import MovingAverageCrossover
from tracker.performance import PerformanceTracker


class ScriptedStrategy(BaseStrategy):
    # lets us feed the backtester exact signals instead of relying on a
    # real strategy, so SL/TP tests are deterministic

    def __init__(self, signals):
        self.signals = signals

    def generate_signals(self, df):
        result = df.copy()
        result["Signal"] = self.signals
        return result


def _make_df(closes):
    dates = pd.bdate_range(start="2024-01-01", periods=len(closes))
    return pd.DataFrame({
        "Date": dates,
        "Open": closes,
        "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes],
        "Close": closes,
        "Volume": [100000] * len(closes),
    })


def test_stop_loss_triggers_correctly():
    # buy at 100, then price drops just past the stop loss line - should
    # force-close right there
    closes = [100, 100, 100 * (1 - config.STOP_LOSS_PCT) - 1, 90]
    df = _make_df(closes)
    signals = ["BUY", "HOLD", "HOLD", "HOLD"]

    broker = MockBroker(config.INITIAL_BALANCE)
    tracker = PerformanceTracker()
    backtester = Backtester(broker, ScriptedStrategy(signals), tracker)
    backtester.run(df)

    trades = tracker.get_trade_history()
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "STOP_LOSS"
    assert trades[0]["exit_price"] == closes[2]


def test_take_profit_triggers_correctly():
    # same idea but price jumps past the take profit line instead
    closes = [100, 100, 100 * (1 + config.TAKE_PROFIT_PCT) + 1, 115]
    df = _make_df(closes)
    signals = ["BUY", "HOLD", "HOLD", "HOLD"]

    broker = MockBroker(config.INITIAL_BALANCE)
    tracker = PerformanceTracker()
    backtester = Backtester(broker, ScriptedStrategy(signals), tracker)
    backtester.run(df)

    trades = tracker.get_trade_history()
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "TAKE_PROFIT"
    assert trades[0]["exit_price"] == closes[2]


def test_full_backtest_run_completes_without_errors():
    # just making sure a real strategy over a longer series doesn't blow up
    closes = [100 + (i % 10) - 5 + (i * 0.2) for i in range(150)]
    df = _make_df(closes)

    broker = MockBroker(config.INITIAL_BALANCE)
    tracker = PerformanceTracker()
    strategy = MovingAverageCrossover(fast_period=5, slow_period=20)
    backtester = Backtester(broker, strategy, tracker)

    metrics = backtester.run(df)

    expected_keys = {
        "total_trades", "winning_trades", "losing_trades", "win_rate",
        "total_pnl", "average_pnl_per_trade", "best_trade", "worst_trade",
        "max_drawdown",
    }
    assert expected_keys.issubset(metrics.keys())
