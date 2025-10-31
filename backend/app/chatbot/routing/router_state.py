"""
State management for the master routing graph.
Handles intent classification and routing to specialized bots.
"""
from typing import TypedDict, List, Optional, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from app.schemas.intent import IntentType

class RoutingState(TypedDict):
    """State for the master routing graph."""
    
    # Messages are automatically managed by LangGraph
    messages: Annotated[List[BaseMessage], add_messages]
    
    # User/session information
    teacher_id: Optional[str]
    session_id: Optional[str]
    original_query: str
    
    # Intent classification results
    intent: Optional[IntentType]
    confidence: float
    classification_reasoning: Optional[str]

    # Routing information
    complexity: Optional[str]  # "simple" or "complex" - determines if specialist needed
    target_bot: Optional[str]  # "handwriting", "vocabulary", "ideas", "general"
    routing_decision: Optional[str]  # Explanation of routing logic
    needs_specialist: bool  # Whether to route to a specialist bot
    specialist_topic: Optional[str]  # Which specialist topic (handwriting, vocabulary, ideas)
    
    # Bot response
    bot_response: Optional[str]
    bot_type: Optional[str]
    relevant_forms: List[str]
    follow_up_questions: List[str]
    
    # Processing metadata
    processing_steps: List[str]  # Track execution steps
    total_processing_time: float
    needs_clarification: bool
    
    # Error handling
    last_error: Optional[str]
    retry_count: int
    
    # Conversation context
    conversation_depth: int
    previous_intents: List[str]