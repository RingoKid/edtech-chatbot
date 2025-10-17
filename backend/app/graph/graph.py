import os
from langgraph.prebuilt import create_react_agent
from langgraph_dynamodb_checkpoint import DynamoDBSaver
from app.graph.context import Context
from app.config import settings


def create_graph(use_checkpointer: bool = False):
    """
    Factory function to create the graph with proper dependency injection.
    This ensures the graph is created with all dependencies properly initialized.

    Args:
        use_checkpointer: Whether to use a custom DynamoDB checkpointer.
                         Set to False for LangGraph Studio (it handles persistence automatically).
                         Set to True for FastAPI application with custom persistence.

    Returns:
        CompiledStateGraph: The compiled LangGraph agent
    """
    # Get the model from context
    context = Context()
    model = context.model

    system_prompt = "You are a helpful AI teaching assistant for educators."

    checkpointer = None

    if use_checkpointer:
        # Configure boto3 session for DynamoDB
        settings.configure_boto3_for_dynamodb()

        # Initialize the DynamoDB checkpointer
        # The saver will automatically create the table if it does not exist
        checkpointer = DynamoDBSaver(
            table_name=os.environ.get("DYNAMODB_TABLE", "LangGraphReactAgentCheckpoints")
        )

    # Pass the checkpointer to the prebuilt agent factory function
    return create_react_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer,
        prompt=system_prompt
    )


# Create the graph instance at module level for langgraph.json
# LangGraph Studio uses this and handles persistence automatically, so no checkpointer
graph = create_graph(use_checkpointer=False)
