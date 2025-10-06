from langgraph.prebuilt import create_react_agent
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

    # Create the graph using the prebuilt react agent
    return create_react_agent(
        model=model,
        tools=[],
        prompt=system_prompt
    )


# Create the graph instance at module level for langgraph.json
graph = create_graph()
