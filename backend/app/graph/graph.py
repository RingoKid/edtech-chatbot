"""
Main lesson planner graph implementation.
This graph demonstrates LangGraph Studio's interrupt functionality for user interaction.
"""
from typing import Optional
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.state import GraphState
from app.graph.context import Context
from app.config import settings

# Ensure LangSmith is initialized
settings.initialize_langsmith()

# Initialize context
context = Context()


def ask_for_topic(state: GraphState) -> dict:
    """
    Node that asks the user for a topic to create a lesson plan.
    This node sets a flag to interrupt and wait for user input.

    Args:
        state: Current graph state

    Returns:
        Updated state with a message asking for the topic
    """
    question_message = AIMessage(
        content="What lesson plan topic would you like me to help you create? Please provide a subject or theme."
    )

    return {
        "messages": [question_message],
        "needs_user_input": True
    }


def generate_lesson_plan(state: GraphState) -> dict:
    """
    Node that generates a lesson plan based on the user's selected topic.

    Args:
        state: Current graph state with topic_selected

    Returns:
        Updated state with the generated lesson plan
    """
    # Get the topic from state
    topic = state.get("topic_selected", "general education")

    # Get the model from context
    model = context.model

    # Create the prompt
    prompt_messages = [
        HumanMessage(content=f"""You are an educational expert who creates engaging and effective lesson plans.

Create a comprehensive lesson plan for the topic: {topic}

The lesson plan should include:
1. Learning Objectives (3-5 specific, measurable objectives)
2. Materials Needed (list all required materials)
3. Introduction/Hook (5-10 minutes)
4. Main Activities (20-30 minutes with step-by-step instructions)
5. Assessment Methods (how to evaluate student learning)
6. Differentiation Strategies (for different learning levels)
7. Closure/Wrap-up (5 minutes)

Make it engaging, age-appropriate, and aligned with educational best practices.""")
    ]

    # Invoke the model
    response = model.invoke(prompt_messages)

    # Create the lesson plan message
    lesson_plan_message = AIMessage(content=response.content)

    return {
        "messages": [lesson_plan_message],
        "needs_user_input": False
    }


def process_user_response(state: GraphState) -> dict:
    """
    Node that processes the user's topic response and stores it in state.

    Args:
        state: Current graph state with messages

    Returns:
        Updated state with topic_selected
    """
    # Get the latest user message
    messages = state.get("messages", [])
    if messages:
        latest_message = messages[-1]
        if isinstance(latest_message, HumanMessage):
            topic = latest_message.content
            return {
                "topic_selected": topic,
                "needs_user_input": False
            }

    # Fallback if no topic found
    return {
        "topic_selected": "general education",
        "needs_user_input": False
    }


def should_continue(state: GraphState) -> str:
    """
    Conditional edge function to determine the next node.

    Args:
        state: Current graph state

    Returns:
        Name of the next node to execute
    """
    needs_input = state.get("needs_user_input", False)
    topic = state.get("topic_selected")

    if needs_input:
        # Interrupt for user input
        return "interrupt"
    elif topic:
        # We have a topic, generate lesson plan
        return "generate"
    else:
        # Process user response first
        return "process"


def create_graph():
    """
    Create and compile the lesson planner graph.

    Returns:
        Compiled LangGraph application
    """
    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("ask_for_topic", ask_for_topic)
    workflow.add_node("process_user_response", process_user_response)
    workflow.add_node("generate_lesson_plan", generate_lesson_plan)

    # Set entry point
    workflow.add_edge(START, "ask_for_topic")

    # Add conditional edges
    workflow.add_conditional_edges(
        "ask_for_topic",
        should_continue,
        {
            "interrupt": END,  # Pause for user input
            "process": "process_user_response"
        }
    )

    workflow.add_edge("process_user_response", "generate_lesson_plan")
    workflow.add_edge("generate_lesson_plan", END)

    # Compile with interrupt before nodes that need user input
    app = workflow.compile(interrupt_before=["process_user_response"])

    return app


# Create the compiled graph instance
graph = create_graph()