from fastapi import WebSocket, APIRouter
from app.sockets.websocket_manager import manager

router = APIRouter()

@router.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(symbol, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except:
        manager.disconnect(symbol, websocket)
