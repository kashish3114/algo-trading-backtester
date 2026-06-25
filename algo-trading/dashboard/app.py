"""
streamlit dashboard. pick a strategy, pick a data source, see the
chart + equity curve + metrics + trade table.

run with:
    streamlit run dashboard/app.py
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from broker.mock_broker import MockBroker
from engine.backtester import Backtester
from strategies.ma_crossover import MovingAverageCrossover
from strategies.rsi_strategy import RSIStrategy
from tracker.performance import PerformanceTracker
from utils.data_loader import load_csv
from utils.logger import get_logger

logger = get_logger(__name__)

STRATEGY_OPTIONS = {
    "MA Crossover": MovingAverageCrossover,
    "RSI": RSIStrategy,
}


@st.cache_data(show_spinner=False)
def load_sample_data():
    # cached so flipping between strategies doesn't re-read the csv every time
    data_path = os.path.join(os.path.dirname(__file__), "..", config.DATA_FILE)
    return load_csv(data_path)


def load_uploaded_data(uploaded_file):
    # dump it to disk first since load_csv expects a path, not a buffer
    temp_path = os.path.join(
        os.path.dirname(__file__), "..", "results", "_uploaded_dashboard_data.csv"
    )
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return load_csv(temp_path)


def run_backtest(strategy_name, df):
    # fresh broker/tracker each time so switching strategies in the UI
    # doesn't carry over stale state
    strategy_cls = STRATEGY_OPTIONS[strategy_name]
    strategy = strategy_cls()

    broker = MockBroker(config.INITIAL_BALANCE)
    tracker = PerformanceTracker()
    backtester = Backtester(broker, strategy, tracker)
    backtester.run(df)
    return backtester


def render_price_chart(signals_df, strategy_name):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=signals_df["Date"],
        open=signals_df["Open"],
        high=signals_df["High"],
        low=signals_df["Low"],
        close=signals_df["Close"],
        name="Price",
    ))

    buys = signals_df[signals_df["Signal"] == "BUY"]
    sells = signals_df[signals_df["Signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buys["Date"], y=buys["Close"], mode="markers", name="BUY",
        marker=dict(symbol="triangle-up", size=12, color="green"),
    ))
    fig.add_trace(go.Scatter(
        x=sells["Date"], y=sells["Close"], mode="markers", name="SELL",
        marker=dict(symbol="triangle-down", size=12, color="red"),
    ))

    fig.update_layout(
        title=f"{strategy_name} - Price with Signals",
        xaxis_title="Date", yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_equity_curve(equity_curve):
    equity_df = pd.DataFrame(equity_curve)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_df["Date"], y=equity_df["PortfolioValue"],
        mode="lines", name="Portfolio Value", line=dict(color="blue"),
    ))
    fig.update_layout(
        title="Equity Curve", xaxis_title="Date", yaxis_title="Portfolio Value",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_metrics_cards(metrics):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Win Rate", f"{metrics['win_rate']:.2f}%")
    col2.metric("Total PnL", f"{metrics['total_pnl']:.2f}")
    col3.metric("Total Trades", f"{metrics['total_trades']}")
    col4.metric("Best Trade", f"{metrics['best_trade']:.2f}")


def render_trade_history(trades):
    st.subheader("Trade History")
    if trades:
        trades_df = pd.DataFrame(trades)
        # these come in as full timestamps, just show the date part
        for col in ("entry_date", "exit_date"):
            trades_df[col] = pd.to_datetime(trades_df[col]).dt.strftime("%Y-%m-%d")
        st.dataframe(trades_df, use_container_width=True)
    else:
        st.info("No trades were executed during this backtest.")


def main():
    st.set_page_config(page_title="Algo Trading Backtester", layout="wide")
    st.title("Algo Trading Backtester")

    st.sidebar.header("Backtest Configuration")
    strategy_name = st.sidebar.selectbox("Select Strategy", list(STRATEGY_OPTIONS.keys()))

    data_source = st.sidebar.radio("Data Source", ["Use Sample Data", "Upload CSV"])

    try:
        if data_source == "Upload CSV":
            uploaded_file = st.sidebar.file_uploader("Upload OHLC CSV", type=["csv"])
            if uploaded_file is None:
                st.info("Upload a CSV file with columns: Date, Open, High, Low, Close, Volume.")
                return
            df = load_uploaded_data(uploaded_file)
        else:
            df = load_sample_data()

        with st.spinner(f"Running {strategy_name} backtest..."):
            backtester = run_backtest(strategy_name, df)

        metrics = backtester.tracker.calculate_metrics()
        trades = backtester.tracker.get_trade_history()

        render_metrics_cards(metrics)
        render_price_chart(backtester.signals_df, strategy_name)
        render_equity_curve(backtester.equity_curve)
        render_trade_history(trades)

    except Exception as exc:
        logger.error(f"Dashboard error: {exc}")
        st.error(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
