"""
Chat router for the FastAPI application.
Contains HTTP and WebSocket endpoints for chat functionality.
Production logic is delegated to `ChatService`.
"""
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, WebSocket, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.services.chat_service import ChatService
from app.services.chat_history_service import get_chat_history_service
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.schemas.chat_history import (
    ConversationListResponse,
    ConversationSummary,
    ConversationMessagesResponse,
)
from app.schemas.auth import UserInDB
from app.dependencies.auth import get_current_user


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


@router.get("/init", response_model=ChatMessageResponse)
async def init_chat(
    current_user: UserInDB = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Initialize a new chat session and get the greeting message.
    Creates a new thread and returns the initial welcome message.

    **Requires authentication.**
    """
    try:
        return await chat_service.init_chat(user_id=current_user.user_id)

    except Exception as e:
        print(f"Error initializing chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize chat: {str(e)}"
        )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: UserInDB = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    **Requires authentication.**
    """
    try:
        return await chat_service.process_chat_request(
            request=request,
            user_id=current_user.user_id
        )

    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/history", response_model=ConversationListResponse)
async def get_chat_history(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get list of conversation summaries for the authenticated user.

    **Requires authentication.**

    Returns a list of conversations with their titles, previews, and timestamps.
    """
    chat_history_service = get_chat_history_service()
    conversations = await chat_history_service.get_user_conversations(
        user_id=current_user.user_id
    )

    return ConversationListResponse(
        conversations=[
            ConversationSummary(
                thread_id=conv.thread_id,
                title=conv.title,
                last_message_preview=conv.last_message_preview,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]
    )


@router.get("/{thread_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    thread_id: str,
    current_user: UserInDB = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get full message history for a specific conversation.

    **Requires authentication.**

    Returns 403 if the user does not own the thread.
    Returns 404 if the thread does not exist.
    """
    chat_history_service = get_chat_history_service()

    # Verify ownership
    is_owner = await chat_history_service.verify_ownership(
        user_id=current_user.user_id,
        thread_id=thread_id
    )

    if not is_owner:
        # Check if thread exists at all (for another user)
        # If not found for this user, could be 404 or 403
        # For security, we return 403 for both cases to avoid thread enumeration
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation"
        )

    # Get messages from checkpointer
    messages = await chat_service.get_conversation_messages(thread_id=thread_id)

    # If no messages and conversation exists, it might just be initialized
    # Return empty messages list
    return ConversationMessagesResponse(
        thread_id=thread_id,
        messages=messages
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
