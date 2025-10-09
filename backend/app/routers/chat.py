"""
Chat router for the FastAPI application.
Contains HTTP endpoints for chat functionality using LangGraph.
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket

from app.service.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service() -> ChatService:
    """
    Dependency function to get ChatService instance.
    This creates a new instance for each request.
    """
    return ChatService()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    Args:
        request: ChatMessageRequest containing the message and optional thread_id
        chat_service: Injected ChatService instance

    Returns:
        ChatMessageResponse: The AI's response and thread_id
    """
    try:
        return await chat_service.process_chat_request(request)

    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.websocket("/ws/message")
async def websocket_message(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for real-time chat communication.
    Accepts WebSocket connections and handles bidirectional chat messages.

    Args:
        websocket: The WebSocket connection instance
        chat_service: Injected ChatService instance
    """
    await chat_service.handle_websocket_connection(websocket)
