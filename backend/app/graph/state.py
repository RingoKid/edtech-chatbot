from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """
    The unified state object for the entire graph.
    """
    # Messages are handled with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # This key will be populated by the main_router
    task_name: Optional[str]

    # New fields for parameter collection
    parameter_schema_name: Optional[str]  # Name of the schema class (e.g., "HandwritingParams")
    required_parameters: List[str]  # List of param names still needed
    collected_parameters: Dict[str, Any]  # Stores collected {name: value} pairs
    current_question: Optional[str]  # The question currently asked
    collection_error_message: Optional[str]  # Temporary error message for re-asking
