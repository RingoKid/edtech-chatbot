from langgraph.prebuilt import create_react_agent
from langgraph_checkpoint_dynamodb import DynamoDBSaver, DynamoDBConfig
from app.graph.context import Context
from app.config import settings, AppEnv


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

    # Instantiate the checkpointer for local prototyping
    # Configure DynamoDBConfig based on environment
    if settings.app_env == AppEnv.LOCAL:
        config = DynamoDBConfig(
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
    else:
        config = DynamoDBConfig(
            region_name=settings.aws_region
        )

    checkpointer = DynamoDBSaver(config, deploy=True)

    # Create the graph using the prebuilt react agent
    return create_react_agent(
        model=model,
        tools=[],
        prompt=system_prompt,
        checkpointer=checkpointer
    )


# Create the graph instance at module level for langgraph.json
graph = create_graph()
