"""
Vocabulary Bot State Schema.
Defines the state structure for the vocabulary and sentence structure bot graph.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class VocabularyState(TypedDict):
    """
    State schema for the Vocabulary Bot LangGraph.

    This state tracks the complete flow of vocabulary and sentence structure instruction,
    from query analysis through response generation and quality checking.
    """

    # Input/Output Messages
    messages: List[BaseMessage]  # Conversation history with teacher

    # Session Information
    teacher_id: str  # Unique identifier for the teacher
    session_id: str  # Unique identifier for the conversation session

    # Query Analysis
    original_query: str  # The teacher's original question
    query_type: Optional[str]  # Type of vocabulary query: sentence_structure|vocabulary_building|grammar|genre_writing|general
    target_vocabulary: List[str]  # Specific vocabulary words mentioned
    target_genre: Optional[str]  # Writing genre: narrative|informational|opinion|personal_narrative
    grade_level: Optional[str]  # Target grade level: prek|kindergarten|1st_grade|mixed

    # Form Retrieval
    relevant_forms: List[Dict[str, Any]]  # Educational forms (I-L) retrieved from database
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