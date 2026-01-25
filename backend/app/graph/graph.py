"""
Graph definition for v2 architecture - ReAct routing agent with task placeholders.

Architecture:
1. User message comes in
2. Routing agent (ReAct) processes and either:
   - Asks clarifying questions (continues conversation)
   - Calls a routing tool (triggers handoff)
3. If routing tool was called, route to appropriate placeholder node
4. Placeholder node returns "coming soon" and ends conversation
"""

import os

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph_checkpoint_aws import DynamoDBSaver
from langchain_core.messages import AIMessage, ToolMessage

from app.graph.state import GraphState
from app.graph.agents.routing import (
    create_routing_agent,
    TOOL_TO_TASK_TYPE,
)
from app.graph.nodes.placeholders import (
    handwriting_placeholder,
    vocabulary_placeholder,
    idea_generation_placeholder,
)
from app.config import settings


# Configure boto3 to use DynamoDB Local endpoint (for langgraph-checkpoint-aws)
# This must be set before DynamoDBSaver is instantiated
if settings.dynamodb_endpoint_url:
    os.environ['AWS_ENDPOINT_URL_DYNAMODB'] = settings.dynamodb_endpoint_url
    os.environ['AWS_DEFAULT_REGION'] = settings.aws_region


def routing_agent_node(state: GraphState) -> dict:
    """
    Node that runs the routing ReAct agent.

    The agent will either:
    1. Generate a response (greeting, clarification question)
    2. Call a routing tool (indicating user intent is clear)

    Returns state updates including messages and optionally task_type.
    """
    # Create fresh agent instance (stateless)
    agent = create_routing_agent()

    # Invoke the agent with current messages
    result = agent.invoke({"messages": state["messages"]})

    # Extract messages from agent result
    new_messages = result.get("messages", [])

    # Check if a routing tool was called by looking at the last messages
    task_type = None
    for msg in reversed(new_messages):
        # Tool messages indicate a tool was called
        if isinstance(msg, ToolMessage):
            tool_name = msg.name
            if tool_name in TOOL_TO_TASK_TYPE:
                task_type = TOOL_TO_TASK_TYPE[tool_name]
                break

    return {
        "messages": new_messages,
        "task_type": task_type,
        "routing_complete": task_type is not None,
    }


def route_after_agent(state: GraphState) -> str:
    """
    Routing function: decide where to go after the routing agent runs.

    If a routing tool was called (task_type is set), go to the appropriate
    placeholder node. Otherwise, end the graph (agent will continue on next invoke).
    """
    task_type = state.get("task_type")

    if task_type == "handwriting":
        return "handwriting_placeholder"
    elif task_type == "vocabulary":
        return "vocabulary_placeholder"
    elif task_type == "idea_generation":
        return "idea_generation_placeholder"
    else:
        # No routing tool called - agent asked a question or greeted
        # End this invocation; user will respond and invoke again
        return END


async def create_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    Factory function to create the graph with proper dependency injection.

    Args:
        checkpointer: Optional checkpointer for state persistence.
                      If None, creates a DynamoDBSaver.

    Returns:
        CompiledStateGraph: The compiled LangGraph
    """
    # Use provided checkpointer or create DynamoDB one
    if checkpointer is None:
        checkpointer = DynamoDBSaver(
            table_name=settings.checkpoint_table_name,
            region_name=settings.aws_region
        )

    # Create the state graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("routing_agent", routing_agent_node)
    graph.add_node("handwriting_placeholder", handwriting_placeholder)
    graph.add_node("vocabulary_placeholder", vocabulary_placeholder)
    graph.add_node("idea_generation_placeholder", idea_generation_placeholder)

    # Set entry point
    graph.set_entry_point("routing_agent")

    # Add conditional edges from routing agent
    graph.add_conditional_edges(
        "routing_agent",
        route_after_agent,
        {
            "handwriting_placeholder": "handwriting_placeholder",
            "vocabulary_placeholder": "vocabulary_placeholder",
            "idea_generation_placeholder": "idea_generation_placeholder",
            END: END,
        }
    )

    # Placeholder nodes always end the conversation
    graph.add_edge("handwriting_placeholder", END)
    graph.add_edge("vocabulary_placeholder", END)
    graph.add_edge("idea_generation_placeholder", END)

    # Compile the graph
    # Note: No interrupt_after needed - the ReAct agent naturally returns
    # after generating a response, and we call it again on next user message
    return graph.compile(checkpointer=checkpointer)


# Create the graph instance at module level for langgraph.json
# Note: This needs to be called with await in an async context
graph = create_graph
