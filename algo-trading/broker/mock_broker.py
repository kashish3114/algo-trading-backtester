"""
fake broker. tracks cash and positions in memory, no real orders go
anywhere. good enough for backtesting.
"""

from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class MockBroker:

    def __init__(self, initial_balance):
        self.balance = float(initial_balance)
        self.positions = {}  # symbol -> {"quantity": int, "avg_price": float}
        self._order_counter = 0
        logger.info(f"MockBroker initialized with balance={self.balance}")

    def _next_order_id(self):
        self._order_counter += 1
        return self._order_counter

    def place_order(self, symbol, quantity, side, price, timestamp=None):
        # BUY: spend cash, grow the position. SELL: get cash back, shrink it.
        # blows up with ValueError if you don't have the cash or the shares.
        try:
            side = side.upper()
            if side not in ("BUY", "SELL"):
                raise ValueError(f"Invalid order side: {side}. Must be 'BUY' or 'SELL'.")

            if quantity <= 0:
                raise ValueError(f"Order quantity must be positive, got {quantity}")

            order_timestamp = timestamp if timestamp is not None else datetime.now()

            if side == "BUY":
                cost = quantity * price
                if cost > self.balance:
                    raise ValueError(
                        f"Insufficient balance to BUY {quantity} {symbol} @ {price}: "
                        f"cost={cost:.2f}, available={self.balance:.2f}"
                    )

                self.balance -= cost

                if symbol in self.positions:
                    # already holding some, blend the entry price
                    existing = self.positions[symbol]
                    total_quantity = existing["quantity"] + quantity
                    total_cost = (existing["quantity"] * existing["avg_price"]) + cost
                    self.positions[symbol] = {
                        "quantity": total_quantity,
                        "avg_price": total_cost / total_quantity,
                    }
                else:
                    self.positions[symbol] = {"quantity": quantity, "avg_price": price}

            else:  # SELL
                position = self.positions.get(symbol)
                if position is None or position["quantity"] < quantity:
                    held = position["quantity"] if position else 0
                    raise ValueError(
                        f"Cannot SELL {quantity} {symbol}: only {held} held"
                    )

                proceeds = quantity * price
                self.balance += proceeds

                remaining_quantity = position["quantity"] - quantity
                if remaining_quantity == 0:
                    del self.positions[symbol]
                else:
                    self.positions[symbol] = {
                        "quantity": remaining_quantity,
                        "avg_price": position["avg_price"],
                    }

            order = {
                "order_id": self._next_order_id(),
                "symbol": symbol,
                "quantity": quantity,
                "side": side,
                "price": price,
                "timestamp": order_timestamp,
                "status": "FILLED",
            }

            logger.info(
                f"Order FILLED: {side} {quantity} {symbol} @ {price} "
                f"(order_id={order['order_id']}, balance={self.balance:.2f})"
            )
            return order

        except ValueError as exc:
            logger.error(f"Order REJECTED: {side} {quantity} {symbol} @ {price} - {exc}")
            raise

    def get_positions(self):
        return self.positions

    def get_balance(self):
        return self.balance

    def get_portfolio_value(self, current_price):
        # cash + whatever the open positions are worth at this price.
        # heads up: assumes one symbol at a time, fine for this project
        market_value = sum(pos["quantity"] * current_price for pos in self.positions.values())
        return self.balance + market_value
