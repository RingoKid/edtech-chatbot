"""Graph state for v2 architecture - simplified for agent-based routing."""

from typing import TypedDict, Annotated, List, Optional, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# Task type literals for routing
TaskType = Literal["handwriting", "vocabulary", "idea_generation"]

# Grade level literals for handwriting lessons
GradeLevel = Literal["PreK", "K", "1st"]

# Student level literals for differentiation
StudentLevel = Literal["struggling", "on-level", "advanced"]


class HandwritingParams(TypedDict):
    """
    Parameters for handwriting lesson generation.

    Collected by the param agent before handing off to the generator.
    """
    grade: GradeLevel
    letter: str
    student_level: StudentLevel


class GraphState(TypedDict):
    """
    Unified state object for the routing agent graph.

    v2 Architecture Notes:
    - messages: Full conversation history, managed by add_messages reducer
    - task_type: Set when routing tool is called, indicates destination
    - routing_complete: Signals successful handoff to task agent
    - handwriting_params: Set when param agent collects all handwriting params
    """
    # Messages are handled with add_messages reducer (appends, not replaces)
    messages: Annotated[List[BaseMessage], add_messages]

    # Set by routing tools when user intent is clear
    task_type: Optional[TaskType]

    # Signals that routing has completed and handoff should occur
    routing_complete: bool

    # Handwriting lesson parameters (set by param agent)
    handwriting_params: Optional[HandwritingParams]
