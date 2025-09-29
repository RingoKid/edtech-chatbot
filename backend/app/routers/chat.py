"""
Chat router for the FastAPI application.
Contains endpoints for chat functionality and conversation management.
"""
from fastapi import APIRouter, Depends
from app.service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


def get_chat_service() -> ChatService:
    """
    Dependency factory for ChatService injection.
    """
    return ChatService()


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatMessageResponse)
async def chat(
    chat_message: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatMessageResponse:
    """
    Main chat endpoint that processes user messages and returns AI responses.
    
    Args:
        chat_message (ChatMessageRequest): The chat message containing thread_id and message
        chat_service (ChatService): Injected ChatService instance
        
    Returns:
        ChatMessageResponse: Response from the chat service with thread_id and reply
    """
    # Use placeholder user_id for now - this could be extracted from authentication later
    user_id = "user_placeholder"
    
    response_dict = await chat_service.handle_message(
        user_message=chat_message.message,
        user_id=user_id,
        thread_id=chat_message.thread_id
    )
    
    # Construct and return ChatMessageResponse object
    return ChatMessageResponse(
        thread_id=response_dict["thread_id"],
        reply=response_dict["reply"]
    )
