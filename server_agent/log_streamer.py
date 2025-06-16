import asyncio
import logging
from fastapi import WebSocket
from typing import List

connected_clients: List[WebSocket] = []

# This will be set to the main event loop when FastAPI starts
event_loop: asyncio.AbstractEventLoop | None = None

async def broadcast_log(message: str):
    to_remove = []
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            to_remove.append(client)

    for client in to_remove:
        connected_clients.remove(client)

def register_client(websocket: WebSocket):
    connected_clients.append(websocket)

def unregister_client(websocket: WebSocket):
    if websocket in connected_clients:
        connected_clients.remove(websocket)

class WebSocketLogHandler(logging.Handler):
    """Logging handler that sends logs to connected WebSocket clients."""
    def emit(self, record):
        log_entry = self.format(record)
        # Ensure this runs in the main event loop (FastAPI)
        if event_loop and event_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_log(log_entry), event_loop)
