import os

from langgraph.graph import StateGraph, END
from langgraph_checkpoint_aws import DynamoDBSaver

from app.graph.state import GraphState
from app.graph.nodes import (
    greeting_node,
    main_router,
    clarification_node,
    setup_handwriting,
    setup_vocabulary,
    setup_idea_generation,
    collect_parameters_node,
    wait_for_user_input,
    stub_generate_lesson_node,
    route_from_main_router,
    route_parameter_collection
)
from app.config import settings

# Configure boto3 to use DynamoDB Local endpoint (for langgraph-checkpoint-aws)
# This must be set before DynamoDBSaver is instantiated
if settings.dynamodb_endpoint_url:
    os.environ['AWS_ENDPOINT_URL_DYNAMODB'] = settings.dynamodb_endpoint_url
    os.environ['AWS_DEFAULT_REGION'] = settings.aws_region


async def create_graph():
    """
    Factory function to create the graph with proper dependency injection.
    This ensures the graph is created with all dependencies properly initialized.

    Returns:
        CompiledStateGraph: The compiled LangGraph agent
    """
    # Use DynamoDBSaver for persistent checkpointing
    # This stores conversation state in DynamoDB (Local or AWS based on environment)
    checkpointer = DynamoDBSaver(
        table_name=settings.checkpoint_table_name,
        region_name=settings.aws_region
    )

    # Create the state graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("greeting_node", greeting_node)
    graph.add_node("main_router", main_router)
    graph.add_node("clarification", clarification_node)
    graph.add_node("setup_handwriting", setup_handwriting)
    graph.add_node("setup_vocabulary", setup_vocabulary)
    graph.add_node("setup_idea_generation", setup_idea_generation)
    graph.add_node("collect_parameters", collect_parameters_node)
    graph.add_node("wait_for_input", wait_for_user_input)
    graph.add_node("generate_lesson", stub_generate_lesson_node)

    # Add edges
    graph.set_entry_point("greeting_node")
    graph.add_edge("greeting_node", "main_router")
    graph.add_conditional_edges(
        "main_router",
        route_from_main_router,
        {
            "handwriting": "setup_handwriting",
            "vocabulary": "setup_vocabulary",
            "idea_generation": "setup_idea_generation",
            "clarification": "clarification"  # Route to clarification node
        }
    )
    graph.add_edge("clarification", "main_router")  # Loop back to main_router after clarification
    
    # Add edges for parameter collection flow
    graph.add_edge("setup_handwriting", "collect_parameters")
    graph.add_edge("setup_vocabulary", "collect_parameters")
    graph.add_edge("setup_idea_generation", "collect_parameters")
    graph.add_conditional_edges(
        "collect_parameters",
        route_parameter_collection,
        {
            "wait_for_input": "wait_for_input",
            "generate_lesson": "generate_lesson"
        }
    )
    graph.add_edge("wait_for_input", "collect_parameters")  # Loop back after user input
    graph.add_edge("generate_lesson", END)

    # Compile the graph with checkpointer and interrupt_after
    # Interrupt after greeting_node, clarification, and wait_for_input
    # wait_for_input is where we pause to wait for user's parameter responses
    return graph.compile(checkpointer=checkpointer, interrupt_after=["greeting_node", "clarification", "wait_for_input"])


# Create the graph instance at module level for langgraph.json
# Note: This needs to be called with await in an async context
graph = create_graph
