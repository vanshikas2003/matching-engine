from typing import Dict, List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, symbol: str, websocket: WebSocket):
        await websocket.accept()
        if symbol not in self.connections:
            self.connections[symbol] = []
        self.connections[symbol].append(websocket)

    def disconnect(self, symbol: str, websocket: WebSocket):
        self.connections[symbol].remove(websocket)

    async def broadcast(self, symbol: str, message: dict):
        if symbol in self.connections:
            for ws in self.connections[symbol]:
                await ws.send_json(message)

manager = WebSocketManager()
