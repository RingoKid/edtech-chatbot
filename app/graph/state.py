from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    """Unified conversation/flow state."""

    # Conversation messages; structure left generic to avoid framework coupling
    messages: List[Dict[str, Any]]

    # Task routing
    task_name: Optional[str]

    # Parameter collection fields
    parameter_schema_name: Optional[str]
    required_parameters: List[str]
    collected_parameters: Dict[str, Any]
    current_question: Optional[str]
    collection_error_message: Optional[str]

    # Lesson generation fields
    prompt_metadata: Optional[Dict[str, Any]]
    generated_lesson: Optional[Dict[str, Any]]


