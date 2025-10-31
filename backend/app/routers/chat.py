"""
Chat router for the FastAPI application.
Contains HTTP and WebSocket endpoints for chat functionality.
Production logic is delegated to `ChatService`.
"""
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.service.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


router = APIRouter(prefix="/chat", tags=["Chat"])


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """
    Returns a singleton ChatService instance for the application lifecycle.
    Uses lru_cache to ensure only one instance is created and reused across requests.
    Can be overridden in tests via dependency injection to avoid event loop conflicts.
    """
    return ChatService()


@router.get("/", tags=["Chat"])
def get_chat_status():
    """
    Simple status endpoint for the chat router (returns at /api/v1/chat).
    """
    return {"router": "chat", "status": "active", "message": "Chat router is working"}


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    This is the production endpoint backed by ChatService.
    """
    try:
        return await chat_service.process_chat_request(request)

    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/ws/info", summary="WebSocket Connection Information")
async def websocket_info():
    """
    Get information about the WebSocket endpoint for real-time chat.

    **WebSocket Endpoint:** `/api/v1/chat/ws/message`
    """
    return JSONResponse(content={
        "endpoint": "/api/v1/chat/ws/message",
        "protocol": "WebSocket",
        "message_format": {
            "request": {
                "message": "string (required)",
                "thread_id": "string (optional)"
            },
            "response": {
                "response": "string",
                "thread_id": "string"
            },
            "error": {
                "error": "string"
            }
        },
        "example_urls": {
            "local": "ws://localhost:8000/api/v1/chat/ws/message",
            "production": "wss://your-domain.com/api/v1/chat/ws/message"
        },
        "usage": "Connect using WebSocket client and send/receive JSON messages"
    })


@router.websocket("/ws/message")
async def websocket_message(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for real-time chat communication.
    Accepts WebSocket connections and handles bidirectional chat messages.
    """
    await chat_service.handle_websocket_connection(websocket)
