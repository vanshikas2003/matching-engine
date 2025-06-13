from fastapi import FastAPI, HTTPException
from .models.order import Order
from .engine.order_book import OrderBook
from fastapi import WebSocket, WebSocketDisconnect
from .sockets.websocket_manager import WebSocketManager

manager = WebSocketManager()

app = FastAPI()

# Global order books by symbol
order_books = {}

def get_order_book(symbol: str) -> OrderBook:
    if symbol not in order_books:
        order_books[symbol] = OrderBook(symbol)
    return order_books[symbol]

@app.get("/")
def read_root():
    return {"status": "Matching engine is ready!"}


@app.post("/orders")
def place_order(order: Order):
    order_book = get_order_book(order.symbol)
    try:
        trades = order_book.add_order(order)
        return {"order_id": order.id, "trades": trades}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bbo/{symbol}")
def get_bbo(symbol: str):
    order_book = get_order_book(symbol)
    bid, ask = order_book.get_bbo()
    return {
        "symbol": symbol,
        "best_bid": bid,
        "best_ask": ask
    }

@app.get("/depth/{symbol}")
def get_depth(symbol: str):
    order_book = get_order_book(symbol)
    return {
        "symbol": symbol,
        "depth": order_book.get_depth()
    }

@app.websocket("/ws/trades/{symbol}")
async def trade_ws(websocket: WebSocket, symbol: str):
    await manager.connect(symbol, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(symbol, websocket)

@app.websocket("/ws/depth/{symbol}")
async def depth_ws(websocket: WebSocket, symbol: str):
    await manager.connect(symbol, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(symbol, websocket)

from app.routes import order  # Import the router
app.include_router(order.router)  # Register the router
