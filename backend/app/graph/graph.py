from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite
from app.graph.state import GraphState
from app.graph.nodes import (
    greeting_node,
    main_router,
    stub_handwriting_node,
    stub_vocabulary_node,
    stub_idea_generation_node,
    route_from_main_router
)


async def create_graph():
    """
    Factory function to create the graph with proper dependency injection.
    This ensures the graph is created with all dependencies properly initialized.

    Returns:
        CompiledStateGraph: The compiled LangGraph agent
    """
    # Use AsyncSqliteSaver for persistent checkpointing across runs
    # This stores conversation state in a SQLite database file
    conn = await aiosqlite.connect("checkpointer.sqlite")
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()

    # Create the state graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("greeting_node", greeting_node)
    graph.add_node("main_router", main_router)
    graph.add_node("handwriting", stub_handwriting_node)
    graph.add_node("vocabulary", stub_vocabulary_node)
    graph.add_node("idea_generation", stub_idea_generation_node)

    # Add edges
    graph.set_entry_point("greeting_node")
    graph.add_edge("greeting_node", "main_router")
    graph.add_conditional_edges(
        "main_router",
        route_from_main_router,
        {
            "handwriting": "handwriting",
            "vocabulary": "vocabulary",
            "idea_generation": "idea_generation",
            "greeting_node": "greeting_node"
        }
    )
    graph.add_edge("handwriting", END)
    graph.add_edge("vocabulary", END)
    graph.add_edge("idea_generation", END)

    # Compile the graph with checkpointer and interrupt_after
    return graph.compile(checkpointer=checkpointer, interrupt_after=["greeting_node"])


# Create the graph instance at module level for langgraph.json
# Note: This needs to be called with await in an async context
graph = create_graph
