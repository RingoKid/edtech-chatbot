"""
Chat router for the FastAPI application.
Contains HTTP endpoints for chat functionality using LangGraph.
"""
from fastapi import APIRouter, HTTPException

from app.service.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize the chat service
chat_service = ChatService()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    Args:
        request: ChatMessageRequest containing the message and optional thread_id

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
