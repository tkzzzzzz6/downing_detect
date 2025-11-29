"""WebSocket connection manager for real-time communication"""
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket
from loguru import logger


class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages to all connected clients"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def send_frame_update(self, frame_data: Dict[str, Any]):
        """Broadcast frame update to all clients"""
        message = {
            "type": "frame",
            **frame_data
        }
        await self.broadcast(message)

    async def send_alert(self, alert_data: Dict[str, Any]):
        """Broadcast alert to all clients"""
        message = {
            "type": "alert",
            "severity": "warning",
            **alert_data
        }
        await self.broadcast(message)

    async def send_status(self, status: str, message_text: str):
        """Broadcast status update to all clients"""
        message = {
            "type": "status",
            "status": status,
            "message": message_text
        }
        await self.broadcast(message)

    async def send_error(self, error: str, details: str = None):
        """Broadcast error to all clients"""
        message = {
            "type": "error",
            "error": error,
            "details": details
        }
        await self.broadcast(message)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
