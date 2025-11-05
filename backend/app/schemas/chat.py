"""
Chat-related Pydantic schemas for request and response models.
Contains data transfer objects for chat functionality.
"""

from pydantic import BaseModel
from typing import Optional, List


class ChatMessageRequest(BaseModel):
    """
    Pydantic model for chat message requests.
    """
    thread_id: Optional[str] = None
    message: str


class ChatMessageResponse(BaseModel):
    """
    Pydantic model for chat message responses.
    """
    thread_id: str
    reply: str


class ChatMessage(BaseModel):
    """
    Individual message in chat history.
    """
    id: int
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatMetadata(BaseModel):
    """
    Metadata about the conversation.
    """
    bot_type: Optional[str] = None
    target_letters: Optional[List[str]] = None
    grade_level: Optional[str] = None
    intent: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """
    Complete chat history response for a conversation thread.
    """
    thread_id: str
    message_count: int
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    metadata: ChatMetadata
    messages: List[ChatMessage]