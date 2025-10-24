"""
State management for the Handwriting and Spelling Bot.
Defines the state structure used throughout the graph execution.
"""
from typing import TypedDict, List, Optional, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class HandwritingState(TypedDict):
    """State for the handwriting and spelling bot graph."""
    
    # Messages are automatically managed by LangGraph
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Teacher and session information
    teacher_id: Optional[str]
    session_id: Optional[str]
    
    # Query analysis
    original_query: str
    query_type: Optional[str]  # "letter_formation", "fine_motor", "spelling", "assessment", "general"
    target_letters: List[str]  # Specific letters mentioned (e.g., ["A", "B", "z"])
    grade_level: Optional[str]  # "prek", "kindergarten", "1st_grade"
    
    # Form retrieval results
    relevant_forms: List[Dict[str, Any]]  # Forms A-H content
    form_context: str  # Processed context from forms
    
    # Response generation
    response_generated: bool
    response_quality_check: bool
    
    # Error handling and retry logic
    retry_count: int
    last_error: Optional[str]
    needs_human_escalation: bool
    
    # Conversation depth and context
    conversation_depth: int
    previous_topics: List[str]
    follow_up_questions: List[str]