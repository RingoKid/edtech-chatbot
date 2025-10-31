"""
Intent classification schemas for the educational chatbot routing system.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

class IntentType(str, Enum):
    HANDWRITING = "handwriting"
    VOCABULARY = "vocabulary"
    IDEAS = "ideas"
    GENERAL = "general"
    OUT_OF_SCOPE = "out_of_scope"

class IntentRequest(BaseModel):
    """Request model for intent classification."""
    message: str = Field(..., min_length=1, max_length=1000, description="Teacher's question or message")
    
class IntentResult(BaseModel):
    """Result of intent classification."""
    intent: IntentType = Field(..., description="Classified intent type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: Optional[str] = Field(None, description="Brief explanation of the classification")
    suggested_forms: Optional[List[str]] = Field(None, description="Suggested form categories for this intent")

class ChatRequest(BaseModel):
    """Request model for complete chat flow."""
    message: str = Field(..., min_length=1, max_length=1000, description="Teacher's question or message")
    teacher_id: Optional[str] = Field(default="teacher_001", description="Unique teacher identifier")
    session_id: Optional[str] = Field(default="session_001", description="Conversation session identifier")
    
class BotResponse(BaseModel):
    """Response from a specialized bot."""
    response: str = Field(..., description="Bot's response to the query")
    bot_type: str = Field(..., description="Type of bot that generated the response")
    relevant_forms: Optional[List[str]] = Field(None, description="Form categories used in the response")
    follow_up_questions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

class ChatResponse(BaseModel):
    """Complete chat response with intent and bot response."""
    intent: IntentType = Field(..., description="Classified intent")
    confidence: float = Field(..., description="Classification confidence")
    response: str = Field(..., description="Bot's response")
    bot_type: str = Field(..., description="Type of bot used")
    relevant_forms: Optional[List[str]] = Field(None, description="Forms referenced")
    follow_up_questions: Optional[List[str]] = Field(None, description="Follow-up suggestions")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time")