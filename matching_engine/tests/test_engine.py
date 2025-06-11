from app.engine.order_book import OrderBook
from app.models.order import Order, OrderSide, OrderType
import pytest

@pytest.mark.asyncio
async def test_limit_order_matching():
    book = OrderBook("BTC-USDT")
    buy_order = Order(id="1", symbol="BTC-USDT", type=OrderType.limit, side=OrderSide.buy, price=100, quantity=2)
    sell_order = Order(id="2", symbol="BTC-USDT", type=OrderType.limit, side=OrderSide.sell, price=100, quantity=2)
    await book.add_order(buy_order)
    trades = await book.add_order(sell_order)
    assert trades[0]['quantity'] == 2
    assert trades[0]['price'] == 100
