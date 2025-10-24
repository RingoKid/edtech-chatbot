"""
Ideas Bot State Schema.
Defines the state structure for the idea generation and organization bot graph.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class IdeasState(TypedDict):
    """
    State schema for the Ideas Bot LangGraph.

    This state tracks the complete flow of idea generation and organization instruction,
    from query analysis through response generation and quality checking.
    """

    # Input/Output Messages
    messages: List[BaseMessage]  # Conversation history with teacher

    # Session Information
    teacher_id: str  # Unique identifier for the teacher
    session_id: str  # Unique identifier for the conversation session

    # Query Analysis
    original_query: str  # The teacher's original question
    query_type: Optional[str]  # Type of ideas query: idea_generation|organization|genre_elements|brainstorming|general
    target_genre: Optional[str]  # Writing genre: narrative|informational|opinion|personal_narrative|compare_contrast
    target_topic: Optional[str]  # Specific writing topic or theme
    grade_level: Optional[str]  # Target grade level: prek|kindergarten|1st_grade|mixed

    # Form Retrieval
    relevant_forms: List[Dict[str, Any]]  # Educational forms (M-Q) retrieved from database
    form_context: str  # Formatted context string for LLM consumption

    # Response Generation
    response_generated: bool  # Whether a response has been generated
    needs_clarification: bool  # Whether clarification questions were sent

    # Quality Control
    response_quality_check: bool  # Whether quality check has been performed
    quality_score: Optional[int]  # Quality score (1-10)
    needs_improvement: bool  # Whether response needs to be regenerated

    # Follow-up
    follow_up_questions: List[str]  # Suggested follow-up questions for the teacher

    # Error Handling
    retry_count: int  # Number of retry attempts
    last_error: Optional[str]  # Last error message
    needs_human_escalation: bool  # Whether human support is needed

    # Conversation Context
    conversation_depth: int  # Number of conversation turns
    previous_topics: List[str]  # Previously discussed topics in this session