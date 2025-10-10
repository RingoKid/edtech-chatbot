from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    State schema for the chatbot graph.

    Attributes:
        messages: List of conversation messages (automatically managed by LangGraph)
    """
    # Messages are handled with add_messages reducer for proper message management
    messages: Annotated[List[BaseMessage], add_messages]
