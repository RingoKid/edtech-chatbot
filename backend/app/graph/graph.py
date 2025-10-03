from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableConfig
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from app.graph.state import GraphState
from app.graph.prompts import TOPIC_SELECTION_PROMPT, SYSTEM_PROMPT
from app.config import settings


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

        # Initialize the model (handle both with and without API key)
        try:
            if settings.openai_api_key:
                model = ChatOpenAI(
                    model="gpt-4o",
                    api_key=settings.openai_api_key.get_secret_value()
                )
            else:
                # Fallback for when API key is not available
                model = ChatOpenAI(model="gpt-4o")
        except Exception as e:
            # If model initialization fails, return error message
            error_message = AIMessage(
                content=f"Error initializing AI model: {str(e)}. Please ensure OPENAI_API_KEY is set."
            )
            return {
                "messages": messages + [error_message],
                "needs_user_input": False
            }

        # Create messages for LLM call
        model_messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"The user selected: {user_input}. Please acknowledge their selection and provide a lesson plan.")
        ]

        # Make the LLM call
        model_response = await model.ainvoke(model_messages)

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