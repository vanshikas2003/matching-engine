from ..engine.order_book import OrderBook
from ..models.order import OrderRequest, Order
import uuid

class EngineManager:
    def __init__(self):
        self.books = {}

    def get_order_book(self, symbol):
        if symbol not in self.books:
            self.books[symbol] = OrderBook(symbol)
        return self.books[symbol]

    async def submit_order(self, order_req: OrderRequest):
        order = Order(
            id=str(uuid.uuid4()),
            symbol=order_req.symbol,
            side=order_req.side,
            type=order_req.order_type,
            quantity=order_req.quantity,
            price=order_req.price
        )
        book = self.get_order_book(order.symbol)
        return await book.add_order(order)

engine_manager = EngineManager()
