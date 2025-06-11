from collections import deque, defaultdict
from app.models.order import Order, OrderSide, OrderType
from sortedcontainers import SortedDict
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from app.sockets.websocket_manager import manager
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: SortedDict = SortedDict(lambda x: -x)  # Highest price first
        self.asks: SortedDict = SortedDict()              # Lowest price first
        self.trade_log: List[dict] = []
        self.stop_orders: List[Order] = []
        self.stop_orders = []

    def _check_and_activate_stop_orders(self):
        best_bid, best_ask = self.get_bbo()
        current_price = best_ask[0] if best_ask else None

        to_activate = []
        for order in list(self.stop_orders):
            if not order.trigger_price:
                continue

        if order.type == OrderType.stop_loss and order.side == OrderSide.sell and current_price <= order.trigger_price:
            order.type = OrderType.market
            to_activate.append(order)
        elif order.type == OrderType.stop_loss and order.side == OrderSide.buy and current_price >= order.trigger_price:
            order.type = OrderType.market
            to_activate.append(order)
        elif order.type == OrderType.stop_limit and order.side == OrderSide.sell and current_price <= order.trigger_price:
            order.type = OrderType.limit
            to_activate.append(order)
        elif order.type == OrderType.stop_limit and order.side == OrderSide.buy and current_price >= order.trigger_price:
            order.type = OrderType.limit
            to_activate.append(order)
        elif order.type == OrderType.take_profit and current_price >= order.trigger_price:
            order.type = OrderType.market
            to_activate.append(order)

        for order in to_activate:
            self.stop_orders.remove(order)
            asyncio.create_task(self.add_order(order))  # Re-process as market or limit order


    async def add_order(self, order: Order) -> List[dict]:
        """Process and match incoming order and broadcast updates."""
        logger.info(f"Order received: {order}")
        trades = []

        # Input validation
        if order.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if order.type in {OrderType.stop_loss, OrderType.stop_limit, OrderType.take_profit}:
            self.stop_orders.append(order)
            return []


        if order.type in {OrderType.limit, OrderType.ioc, OrderType.fok} and order.price is None:
            raise ValueError("Price is required for this order type")

        if order.type == OrderType.market:
            trades = self._execute_market_order(order)

        elif order.type == OrderType.limit:
            trades = self._execute_limit_order(order, rest_on_book=True)

        elif order.type == OrderType.ioc:
            trades = self._execute_limit_order(order, rest_on_book=False)

        elif order.type == OrderType.fok:
            if self._can_fully_fill(order):
                trades = self._execute_limit_order(order, rest_on_book=False)

        self.trade_log.extend(trades)
        logger.info(f"Executed trades: {trades}")

        for trade in trades:
            await manager.broadcast(self.symbol, {
                "type": "trade",
                "trade": trade
            })

        await manager.broadcast(self.symbol, {
            "type": "depth_update",
            "depth": self.get_depth(),
            "bbo": self.get_bbo()
        })

        return trades

    def _execute_market_order(self, order: Order) -> List[dict]:
        return self._match(order, is_market=True)

    def _execute_limit_order(self, order: Order, rest_on_book: bool) -> List[dict]:
        trades = self._match(order)
        if rest_on_book and order.quantity > 0:
            self._add_to_book(order)
        return trades
    
        self._check_and_activate_stop_orders()

    

    def _can_fully_fill(self, order: Order) -> bool:
        remaining = order.quantity
        book = self.asks if order.side == OrderSide.buy else self.bids
        for price_level in book:
            queue = book[price_level]
            for resting_order in queue:
                remaining -= resting_order.quantity
                if remaining <= 0:
                    return True
        return False

    def _match(self, order: Order, is_market=False) -> List[dict]:
        trades = []
        book = self.asks if order.side == OrderSide.buy else self.bids
        price_check = (
            (lambda p: p <= order.price) if order.side == OrderSide.buy else (lambda p: p >= order.price)
        )

        for price_level in list(book.keys()):
            if is_market or price_check(price_level):
                queue = book[price_level]
                while queue and order.quantity > 0:
                    resting_order = queue[0]
                    traded_qty = min(order.quantity, resting_order.quantity)
                    trade_price = price_level
                    trade = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "symbol": order.symbol,
                        "trade_id": str(uuid4()),
                        "price": str(trade_price),
                        "quantity": traded_qty,
                        "aggressor_side": order.side,
                        "maker_order_id": resting_order.id,
                        "taker_order_id": order.id,
                    }
                    trades.append(trade)

                    order.quantity -= traded_qty
                    resting_order.quantity -= traded_qty

                    if resting_order.quantity == 0:
                        queue.popleft()

                if not queue:
                    del book[price_level]

                if order.quantity == 0:
                    break
            else:
                break
        return trades
    
        self._check_and_activate_stop_orders()


    def _add_to_book(self, order: Order):
        book = self.bids if order.side == OrderSide.buy else self.asks
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(order)

    def get_bbo(self) -> Dict[str, Optional[Tuple[str, float]]]:
        best_bid = (
            (str(self.bids.peekitem(0)[0]), sum(order.quantity for order in self.bids.peekitem(0)[1]))
            if self.bids else None
        )
        best_ask = (
            (str(self.asks.peekitem(0)[0]), sum(order.quantity for order in self.asks.peekitem(0)[1]))
            if self.asks else None
        )
        return {
            "best_bid": best_bid,
            "best_ask": best_ask
        }

    def get_depth(self, levels=10) -> Dict[str, List[Tuple[str, float]]]:
        def aggregate(book):
            depth = []
            for price, orders in list(book.items())[:levels]:
                total_quantity = sum(order.quantity for order in orders)
                depth.append((str(price), total_quantity))
            return depth

        return {
            "bids": aggregate(self.bids),
            "asks": aggregate(self.asks)
        }
    
    
    
    
