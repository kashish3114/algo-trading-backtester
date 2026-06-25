"""
tests for the mock broker.
"""

import pytest

from broker.mock_broker import MockBroker


def test_place_order_buy_reduces_balance():
    broker = MockBroker(initial_balance=10000)
    order = broker.place_order("DEMO", 10, "BUY", 100)

    assert order["status"] == "FILLED"
    assert broker.get_balance() == 10000 - (10 * 100)
    assert broker.get_positions()["DEMO"]["quantity"] == 10


def test_place_order_sell_increases_balance():
    broker = MockBroker(initial_balance=10000)
    broker.place_order("DEMO", 10, "BUY", 100)
    balance_after_buy = broker.get_balance()

    broker.place_order("DEMO", 10, "SELL", 110)

    assert broker.get_balance() == balance_after_buy + (10 * 110)
    assert "DEMO" not in broker.get_positions()


def test_insufficient_balance_raises_error():
    broker = MockBroker(initial_balance=100)

    with pytest.raises(ValueError):
        broker.place_order("DEMO", 10, "BUY", 100)  # costs 1000, only have 100


def test_selling_nonexistent_position_raises_error():
    broker = MockBroker(initial_balance=10000)

    with pytest.raises(ValueError):
        broker.place_order("DEMO", 10, "SELL", 100)  # never bought anything


def test_get_portfolio_value():
    broker = MockBroker(initial_balance=10000)
    broker.place_order("DEMO", 10, "BUY", 100)

    expected_value = broker.get_balance() + (10 * 120)
    assert broker.get_portfolio_value(120) == expected_value
