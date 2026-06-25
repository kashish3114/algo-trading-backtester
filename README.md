# Algo Trading Backtester

A backtesting framework for testing trading strategies against historical price data.
You give it OHLC data, it simulates trades day by day through a fake broker, and
tells you how the strategy would have performed — PnL, win rate, drawdown, the works.
No real money, no exchange connections, just a clean simulation.

Built for a software developer assessment. No external trading libraries used —
MA and RSI are both implemented from scratch using pandas and numpy.

---

## What's implemented

Two strategies:

**Moving Average Crossover** — computes a fast (10-day) and slow (50-day) rolling
average on closing prices. Buys when the fast MA crosses above the slow one (golden
cross), sells when it crosses below (death cross). Trend-following logic — works well
in sustained moves, gets chopped up in sideways markets.

**RSI Strategy** — calculates RSI using Wilder's smoothing method from scratch.
Buys when RSI drops below 30 (oversold, expect a bounce), sells when it rises above
70 (overbought, expect a pullback). Trades less frequently than MA crossover, more
suited to mean-reverting price action.

Both strategies have stop-loss (5%) and take-profit (10%) baked into the backtesting
engine — these are checked before the strategy signal on every bar, so risk is managed
regardless of what the signal says.

---

## Project structure

```
algo-trading/
├── data/
│   ├── sample_data.py       # generates 2 years of fake OHLC data for testing
│   └── OHLC_data.csv        # the generated CSV, committed for convenience
├── strategies/
│   ├── base_strategy.py     # abstract base class, enforces generate_signals() contract
│   ├── ma_crossover.py      # moving average crossover logic
│   └── rsi_strategy.py      # RSI logic, Wilder's smoothing implemented manually
├── broker/
│   └── mock_broker.py       # fake broker: place_order(), get_positions(), get_balance()
├── engine/
│   └── backtester.py        # main loop — risk checks first, then strategy signal
├── tracker/
│   └── performance.py       # tracks trades, calculates PnL, win rate, drawdown
├── utils/
│   ├── data_loader.py       # reads and validates the CSV
│   ├── live_data.py         # pulls real data via yfinance
│   └── logger.py            # logs to console and trading.log
├── tests/                   # 12 unit tests, all passing
├── dashboard/
│   └── app.py               # Streamlit UI
├── results/                 # trade history CSVs get written here after each run
├── config.py                # every magic number lives here, nowhere else
├── main.py                  # entry point
└── requirements.txt
```

---

## Setup

Requires Python 3.11+. Use a virtual environment.

```bash
git clone https://github.com/kashish3114/algo-trading-backtester.git
cd algo-trading

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Generate the sample data (only needed once, the CSV is already committed but
you can regenerate it):

```bash
python data/sample_data.py
```

---

## Running the backtest

**Against the bundled sample data:**
```bash
python main.py
```

**Against a real ticker via yfinance:**
```bash
python main.py --live RELIANCE.NS
```

Any yfinance-supported ticker works — `TATAMOTORS.NS`, `INFY.NS`, `AAPL`, `TSLA`, etc.
The `--live` flag fetches 2 years of daily data, reshapes it to match the internal
DataFrame format, and runs the same pipeline. Everything downstream is identical.

After each run, trade history is saved to `results/ma_crossover_trades.csv` and
`results/rsi_trades.csv`.

---

## Sample output

**On the bundled synthetic dataset (504 trading days):**

```
========== BACKTEST REPORT: MA CROSSOVER ==========
Total Trades        : 7
Winning Trades      : 2
Losing Trades       : 5
Win Rate            : 28.57%
Total PnL           : -1597.50
Average PnL/Trade   : -228.21
Best Trade          : +1036.00  (TAKE_PROFIT, Sep 2025)
Worst Trade         : -649.70   (STOP_LOSS, Jul 2025)
====================================================

========== BACKTEST REPORT: RSI =====================
Total Trades        : 4
Winning Trades      : 2
Losing Trades       : 2
Win Rate            : 50.00%
Total PnL           : +510.50
Average PnL/Trade   : +127.63
Best Trade          : +855.40   (TAKE_PROFIT, Jul 2025)
Worst Trade         : -652.10   (STOP_LOSS, Nov 2024)
====================================================
```

**On RELIANCE.NS live data (499 trading days):**

```
MA Crossover  →  11 trades, 18.18% win rate, PnL: -2499.62
RSI           →   5 trades, 40.00% win rate, PnL:  -259.77
```

The negative PnL isn't a bug — MA Crossover is a trend-following strategy and
the datasets used here have a lot of choppy, sideways price action. The system
works correctly: stop losses trigger at exactly 5% below entry, take profits at
exactly 10% above, and all signals match the strategy logic. A real deployment
would add position sizing and a volatility filter before going anywhere near live
markets with this.

---

## Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `localhost:8501`. Pick a strategy and data source from the sidebar.
Shows a candlestick chart with BUY/SELL markers plotted on it, an equity curve
tracking portfolio value over time, metric cards at the top (win rate, total PnL,
trade count, best trade), and a full trade history table with entry/exit dates,
prices, PnL, and exit reason for every trade.

---

## Tests

```bash
pytest tests/
```

12 tests covering strategies, broker logic, and the backtesting engine.
Includes specific tests for stop-loss and take-profit triggering correctly.

---

## Configuration

Everything is in `config.py`. Change values there — nothing is hardcoded anywhere else.

```python
INITIAL_BALANCE   = 100000    # starting cash
MA_FAST_PERIOD    = 10        # fast moving average window
MA_SLOW_PERIOD    = 50        # slow moving average window
RSI_PERIOD        = 14        # RSI lookback
RSI_OVERSOLD      = 30        # buy threshold
RSI_OVERBOUGHT    = 70        # sell threshold
STOP_LOSS_PCT     = 0.05      # 5% below entry → force close
TAKE_PROFIT_PCT   = 0.10      # 10% above entry → force close
DEFAULT_QUANTITY  = 10        # shares per trade
```

---

## Logging

Every run appends to `trading.log` in the root directory. Covers data loading,
every signal generated, every order placed, and every stop-loss or take-profit
trigger. Useful for tracing exactly why a specific trade happened.

---

## Architecture notes

The system is designed so the strategy, broker, and backtester are completely
independent. Plugging in a new strategy means inheriting from `BaseStrategy` and
implementing `generate_signals(df)` — nothing else in the pipeline needs to change.
The mock broker has the same interface you'd expect from a real broker API
(`place_order`, `get_positions`, `get_balance`), so swapping it for a real one
later would be straightforward.

---

## Dependencies

```
pandas
numpy
matplotlib
streamlit
plotly
pytest
yfinance
```

No backtrader, zipline, ta-lib, or pandas-ta. The MA and RSI calculations are
written from scratch — partly to avoid the dependency, partly because it's more
transparent about what's actually happening under the hood.