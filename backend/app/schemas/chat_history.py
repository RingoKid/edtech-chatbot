"""
API response schemas for chat history endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional


class ConversationSummary(BaseModel):
    """Summary of a conversation for the history list."""
    thread_id: str
    title: str
    last_message_preview: Optional[str] = None
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    """Response model for GET /chat/history."""
    conversations: List[ConversationSummary]


class MessageItem(BaseModel):
    """A single message in a conversation."""
    role: str  # "assistant" or "user"
    content: str
    timestamp: Optional[str] = None


class ConversationMessagesResponse(BaseModel):
    """Response model for GET /chat/{thread_id}/messages."""
    thread_id: str
    messages: List[MessageItem]
