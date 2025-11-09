"""
Graph state definition.
Define the state structure that will be passed between nodes in your graph.

TODO: Update this state definition to match your specific use case
"""

from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    The state object for the graph.

    TODO: Add additional fields as needed for your implementation.
    """
    # Messages are handled with add_messages reducer
    # This is commonly used for conversation history
    messages: Annotated[List[BaseMessage], add_messages]

    # TODO: Add additional state fields here
    # Example:
    # field_name: Optional[str]
    # counter: int
