"""
tests for the MA crossover and RSI strategies.
"""

import pandas as pd

from strategies.ma_crossover import MovingAverageCrossover
from strategies.rsi_strategy import RSIStrategy

VALID_SIGNALS = {"BUY", "SELL", "HOLD"}


def _make_df(closes):
    # quick helper to turn a list of closes into a full OHLC df
    dates = pd.bdate_range(start="2024-01-01", periods=len(closes))
    return pd.DataFrame({
        "Date": dates,
        "Open": closes,
        "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes],
        "Close": closes,
        "Volume": [100000] * len(closes),
    })


def test_ma_crossover_known_data():
    # fast_period=2, slow_period=4 on this price series: the lines cross
    # exactly once on the way up (index 4, BUY) and once on the way down
    # (index 7, SELL) - everything else is just fast staying put, so HOLD
    closes = [10, 10, 10, 10, 20, 20, 20, 20, 5, 5, 5, 5]
    df = _make_df(closes)

    strategy = MovingAverageCrossover(fast_period=2, slow_period=4)
    result = strategy.generate_signals(df)

    buy_indices = [4]
    sell_indices = [7]
    hold_indices = [i for i in range(len(closes)) if i not in buy_indices + sell_indices]

    assert (result.loc[buy_indices, "Signal"] == "BUY").all()
    assert (result.loc[sell_indices, "Signal"] == "SELL").all()
    assert (result.loc[hold_indices, "Signal"] == "HOLD").all()

    assert "MA_Fast" in result.columns
    assert "MA_Slow" in result.columns


def test_rsi_values_within_range():
    # RSI is bounded 0-100 by definition, after the warm-up NaNs are gone
    closes = [100 + (i % 7) - 3 + (i * 0.1) for i in range(60)]
    df = _make_df(closes)

    strategy = RSIStrategy(rsi_period=14)
    result = strategy.generate_signals(df)

    rsi_values = result["RSI"].dropna()
    assert not rsi_values.empty
    assert (rsi_values >= 0).all()
    assert (rsi_values <= 100).all()


def test_signals_only_buy_sell_hold_ma():
    closes = [100 + (i % 5) * 2 - (i % 3) for i in range(80)]
    df = _make_df(closes)

    strategy = MovingAverageCrossover(fast_period=5, slow_period=20)
    result = strategy.generate_signals(df)

    assert set(result["Signal"].unique()).issubset(VALID_SIGNALS)


def test_signals_only_buy_sell_hold_rsi():
    closes = [100 + (i % 9) - 4 + (i * 0.05) for i in range(80)]
    df = _make_df(closes)

    strategy = RSIStrategy(rsi_period=14)
    result = strategy.generate_signals(df)

    assert set(result["Signal"].unique()).issubset(VALID_SIGNALS)
