"""Graph state for v2 architecture - simplified for agent-based routing."""

from typing import TypedDict, Annotated, List, Optional, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# Task type literals for routing
TaskType = Literal["handwriting", "vocabulary", "idea_generation"]


class GraphState(TypedDict):
    """
    Unified state object for the routing agent graph.

    v2 Architecture Notes:
    - messages: Full conversation history, managed by add_messages reducer
    - task_type: Set when routing tool is called, indicates destination
    - routing_complete: Signals successful handoff to task agent
    """
    # Messages are handled with add_messages reducer (appends, not replaces)
    messages: Annotated[List[BaseMessage], add_messages]

    # Set by routing tools when user intent is clear
    task_type: Optional[TaskType]

    # Signals that routing has completed and handoff should occur
    routing_complete: bool
