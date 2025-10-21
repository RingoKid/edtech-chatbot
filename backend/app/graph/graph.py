from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.graph.context import Context


async def create_graph():
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

    # Initialize the async SQLite checkpointer
    # This will create the database file if it doesn't exist
    checkpointer = AsyncSqliteSaver.from_conn_string("checkpointer.sqlite")

    # Pass the checkpointer to the prebuilt agent factory function
    return create_react_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer,
        prompt=system_prompt
    )


# Create the graph instance at module level for langgraph.json
# Note: This needs to be called with await in an async context
graph = create_graph
