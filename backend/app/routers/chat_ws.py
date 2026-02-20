"""
WebSocket router for real-time chat streaming.

Separated from chat.py because WebSocket connections can't use
OAuth2PasswordBearer (no HTTP request headers). Auth is handled
via query parameter token instead.
"""
from functools import lru_cache
from fastapi import APIRouter, WebSocket, Depends
from typing import Optional

from app.services.chat_service import ChatService
from app.dependencies.auth import get_websocket_user
from app.schemas.auth import UserInDB


router = APIRouter(prefix="/chat", tags=["Chat WebSocket"])


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService()


@router.websocket("/ws/message")
async def websocket_message(
    websocket: WebSocket,
    user: Optional[UserInDB] = Depends(get_websocket_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    WebSocket endpoint for real-time chat with token streaming.
    Accepts WebSocket connections and streams LLM response chunks.

    Auth is optional via ?token=<jwt> query parameter.
    """
    await chat_service.handle_websocket_connection(websocket)
