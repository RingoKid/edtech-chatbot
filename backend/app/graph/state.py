from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """
    State schema for the chatbot graph.

    Attributes:
        messages: List of conversation messages (automatically managed by LangGraph)
        user_id: User identifier
        thread_id: Thread identifier for conversation tracking
        forms: List of forms or data structures
        route: Optional routing decision for next node
    """
    # Messages are handled with add_messages reducer for proper message management
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    thread_id: str
    forms: list
    route: Optional[str]


# Keep backward compatibility
GraphState = State
