from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    The unified state object for the entire graph.
    """
    # Messages are handled with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # This key will be populated by the main_router
    task_name: str
