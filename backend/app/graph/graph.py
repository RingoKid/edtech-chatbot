import os
from langgraph.graph import StateGraph, END
from langgraph_dynamodb_checkpoint import DynamoDBSaver
from langchain_core.messages import AIMessage

from app.graph.context import Context
from app.config import settings
from app.graph.state import State
from app.graph.nodes.routing_nodes import greeting_node, Router


# Define placeholder nodes for each task.
def handwriting_node(state: State):
    return {"messages": [AIMessage(content="Routing to handwriting task.")]}


def vocabulary_node(state: State):
    return {"messages": [AIMessage(content="Routing to vocabulary task.")]}


def idea_generation_node(state: State):
    return {"messages": [AIMessage(content="Routing to idea generation task.")]}


def general_node(state: State):
    return {"messages": [AIMessage(content="Routing to general inquiry.")]}


def create_graph(use_checkpointer: bool = True):
    """Factory function to create and compile the main conversational graph."""
    context = Context()
    model = context.model

    checkpointer = None
    if use_checkpointer:
        settings.configure_boto3_for_dynamodb()
        checkpointer = DynamoDBSaver(
            table_name=os.environ.get("DYNAMODB_TABLE", "LangGraphReactAgentCheckpoints")
        )

    router = Router(model)
    graph = StateGraph(State)

    # Add a start node that decides whether to greet or route
    def start_node(state: State) -> dict:
        """Decides whether to show greeting or skip to router."""
        return {}

    # Add all nodes to the graph
    graph.add_node("start", start_node)
    graph.add_node("greeting", greeting_node)
    graph.add_node("router", router.route)
    graph.add_node("handwriting", handwriting_node)
    graph.add_node("vocabulary", vocabulary_node)
    graph.add_node("idea_generation", idea_generation_node)
    graph.add_node("general", general_node)

    # Set standard entry point to start node
    graph.set_entry_point("start")

    # From start, conditionally go to greeting or router
    def route_from_start(state: State) -> str:
        # Check if greeting has been sent
        has_greeting = any(isinstance(msg, AIMessage) and "AI assistant for lesson planning" in msg.content
                           for msg in state["messages"])

        if has_greeting:
            return "router"
        else:
            return "greeting"

    graph.add_conditional_edges(
        "start",
        route_from_start,
        {
            "greeting": "greeting",
            "router": "router"
        }
    )

    # After the greeting, END and wait for user response
    graph.add_edge("greeting", END)

    # From router, go to appropriate task node
    graph.add_conditional_edges(
        "router",
        lambda x: x["route"],
        {
            "handwriting": "handwriting",
            "vocabulary": "vocabulary",
            "idea_generation": "idea_generation",
            "general": "general",
        },
    )

    # For now, all task nodes end the conversation.
    graph.add_edge("handwriting", END)
    graph.add_edge("vocabulary", END)
    graph.add_edge("idea_generation", END)
    graph.add_edge("general", END)

    # Compile the graph with state persistence
    return graph.compile(checkpointer=checkpointer)


# Create the graph instance for LangGraph Studio (no checkpointer needed).
graph = create_graph(use_checkpointer=False)
