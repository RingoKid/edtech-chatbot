import os
import boto3
from langgraph.prebuilt import create_react_agent
from langgraph_dynamodb_checkpoint import DynamoDBSaver
from app.graph.context import Context


def create_graph():
    """
    Factory function to create the graph with proper dependency injection.
    This ensures the graph is created with all dependencies properly initialized.

    Returns:
        CompiledStateGraph: The compiled LangGraph agent
    """
    # Get the model from context
    context = Context()
    model = context.model

    system_prompt = "You are a helpful AI teaching assistant for educators."

    # Configure boto3 to use the local DynamoDB endpoint
    # The DynamoDBSaver creates its own boto3 resource internally,
    # so we need to configure the default boto3 session before instantiation
    boto3.setup_default_session(
        region_name="us-east-1",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy"
    )

    # Set the endpoint URL via environment variable (boto3 will pick this up)
    os.environ['AWS_ENDPOINT_URL_DYNAMODB'] = "http://dynamodb-local:8000"

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
graph = create_graph()
