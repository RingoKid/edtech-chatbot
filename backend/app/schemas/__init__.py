"""
Schemas package for the edtech chatbot application.
Contains Pydantic models for data validation and serialization.
"""

from .chat import ChatMessageRequest, ChatMessageResponse

__all__ = ["ChatMessageRequest", "ChatMessageResponse"]