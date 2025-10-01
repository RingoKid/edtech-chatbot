from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    State schema for the lesson planning graph.

    Attributes:
        messages: List of conversation messages (automatically managed by LangGraph)
        needs_user_input: Flag indicating if the graph should pause for user input
        topic_selected: The topic selected by the user for lesson planning
    """
    # Messages are handled with add_messages reducer for proper message management
    messages: Annotated[List[BaseMessage], add_messages]

    # Control flags for interrupt handling
    needs_user_input: Optional[bool]

    # User selections and data
    topic_selected: Optional[str]
