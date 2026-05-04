from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self) -> None:
        # Map user_id to list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_json(self, message: Any, user_id: str) -> None:
        if user_id not in self.active_connections:
            return
        
        data = json.dumps(message, default=str)
        dead = []
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast_json(self, message: Any) -> None:
        data = json.dumps(message, default=str)
        for user_id in list(self.active_connections.keys()):
            dead = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, user_id)


manager = ConnectionManager()
