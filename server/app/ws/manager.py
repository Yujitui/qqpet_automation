from typing import Dict, Set, Optional
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(ws)

    def disconnect(self, ws: WebSocket, user_id: int):
        if user_id in self._connections:
            self._connections[user_id].discard(ws)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        if user_id not in self._connections:
            return
        dead = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[user_id].discard(ws)
        if user_id in self._connections and not self._connections[user_id]:
            del self._connections[user_id]

    async def broadcast(self, message: dict):
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    def is_online(self, user_id: int) -> bool:
        return user_id in self._connections and bool(self._connections[user_id])

    def get_online_users(self) -> list[int]:
        return [uid for uid, sockets in self._connections.items() if sockets]


manager = ConnectionManager()
