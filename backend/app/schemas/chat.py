"""
Chat-related Pydantic schemas for request and response models.
Contains data transfer objects for chat functionality.
"""

from pydantic import BaseModel
from typing import Optional


class ChatMessageRequest(BaseModel):
    """
    Pydantic model for chat message requests.
    """
    thread_id: Optional[str] = None
    message: str


class ImageReadyEvent(BaseModel):
    """An image that was generated for a lesson."""
    url: str
    placement: str
    alt_text: str


class ChatMessageResponse(BaseModel):
    """
    Pydantic model for chat message responses.
    """
    thread_id: str
    reply: str
    images: Optional[list[ImageReadyEvent]] = None