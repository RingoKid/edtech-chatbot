from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableConfig
from typing import Dict, Any

from app.graph.state import GraphState
from app.graph.prompts import TOPIC_SELECTION_PROMPT
from app.graph.context import Context


async def ask_for_topic_node(state: GraphState, *, config: RunnableConfig) -> Dict[str, Any]:
    """
    Ask for topic node that prompts the user to select a lesson plan topic.
    Uses conditional logic to determine when to interrupt.

    Args:
        state: Current graph state
        config: Configuration containing context with model and system prompt

    Returns:
        Dictionary with updated messages field and control flags
    """
    # Access the context from config
    context: Context = config.get("configurable", {}).get("context")

    messages = state.get("messages", [])

    # If no messages, ask the topic selection question and signal for interrupt
    if not messages:
        topic_message = AIMessage(content=TOPIC_SELECTION_PROMPT)
        return {
            "messages": [topic_message],
            "needs_user_input": True  # Flag to indicate interrupt needed
        }

    # Check if we're waiting for user input
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and state.get("needs_user_input", False):
        # We're waiting for user input, signal interrupt
        return {
            "messages": messages,
            "needs_user_input": True
        }

    # User has responded, process the input
    if isinstance(last_message, HumanMessage):
        user_input = last_message.content

        # Create messages for LLM call
        model_messages = [
            SystemMessage(content=context.system_prompt),
            HumanMessage(content=f"The user selected: {user_input}. Please acknowledge their selection and provide a lesson plan.")
        ]

        # Make the LLM call
        model_response = await context.model.ainvoke(model_messages)

        return {
            "messages": messages + [model_response],
            "needs_user_input": False,  # No longer need user input
            "topic_selected": user_input
        }

    # Fallback
    return {"messages": messages}


def create_graph():
    """
    Create and compile the LangGraph with conditional interrupt capability.

    Returns:
        Compiled StateGraph ready for execution with conditional interrupts
    """
    # Initialize the StateGraph with the state schema
    builder = StateGraph(GraphState)

    # Add nodes to the graph
    builder.add_node("ask_for_topic", ask_for_topic_node)
    
    # Define entry point using START edge
    builder.add_edge(START, "ask_for_topic")

    # Define the flow: ask_for_topic -> END
    builder.add_edge("ask_for_topic", END)
    
    # Compile the graph with interrupt after the node
    # This allows the node to run, show the question, then pause for user input
    graph = builder.compile(interrupt_after=["ask_for_topic"])

    return graph


# Create the compiled graph instance
graph = create_graph()