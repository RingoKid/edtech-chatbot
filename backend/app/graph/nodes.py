from langchain_core.messages import AIMessage, SystemMessage  # type: ignore[import-not-found]
from app.graph.state import GraphState
from app.schemas.task_route import TaskRoute
from app.graph.context import Context
from app.graph.prompts import (
    GREETING_WELCOME_MESSAGE,
    MAIN_ROUTER_SYSTEM_PROMPT,
    MAIN_ROUTER_ERROR_MESSAGE,
    MAIN_ROUTER_CLARIFICATION_MESSAGE,
    HANDWRITING_STUB_MESSAGE,
    VOCABULARY_STUB_MESSAGE,
    IDEA_GENERATION_STUB_MESSAGE,
)


ALLOWED_TASKS = {"Handwriting", "Vocabulary", "Idea Generation"}


def greeting_node(state: GraphState) -> dict:
    """
    Greets the user and presents the main task options.
    """
    welcome_message = AIMessage(content=GREETING_WELCOME_MESSAGE)
    return {"messages": [welcome_message]}


def main_router(state: GraphState) -> dict:
    """
    Routes the user's choice to the appropriate task node.
    Uses structured output with Pydantic to classify the user's intent.
    If the intent is unclear, sets task_name to __CLARIFY__.
    """
    # Get the context and LLM with structured output
    context = Context()
    llm = context.model
    structured_llm = llm.with_structured_output(TaskRoute, strict=True)

    # Get the last message (user's choice)
    last_message = state["messages"][-1]

    # Create a system message to guide the classification
    system_prompt = SystemMessage(content=MAIN_ROUTER_SYSTEM_PROMPT)

    try:
        # Invoke the LLM with structured output, including system prompt
        route = structured_llm.invoke([system_prompt, last_message])
        task_name = route.task_name

        # Check if LLM explicitly requested clarification
        if task_name == "__CLARIFY__":
            print(f"DEBUG: LLM requested clarification")
            return {"task_name": "__CLARIFY__"}
        
        # On successful task classification, update task_name
        print(f"DEBUG: Successfully routed to {task_name}")
        return {"task_name": task_name}
    except Exception as e:
        # On failure (e.g., validation error), treat as clarification needed
        print(f"DEBUG: Routing failed with error: {e}")
        return {"task_name": "__CLARIFY__"}


def clarification_node(state: GraphState) -> dict:
    """
    Sends a clarification message when the user's intent is unclear.
    """
    clarification_message = AIMessage(content=MAIN_ROUTER_CLARIFICATION_MESSAGE)
    return {"messages": [clarification_message]}


def stub_handwriting_node(state: GraphState) -> dict:
    """
    Placeholder for the Handwriting feature.
    """
    stub_message = AIMessage(content=HANDWRITING_STUB_MESSAGE)
    return {"messages": [stub_message]}


def stub_vocabulary_node(state: GraphState) -> dict:
    """
    Placeholder for the Vocabulary feature.
    """
    stub_message = AIMessage(content=VOCABULARY_STUB_MESSAGE)
    return {"messages": [stub_message]}


def stub_idea_generation_node(state: GraphState) -> dict:
    """
    Placeholder for the Idea Generation feature.
    """
    stub_message = AIMessage(content=IDEA_GENERATION_STUB_MESSAGE)
    return {"messages": [stub_message]}


def route_from_main_router(state: GraphState) -> str:
    """
    Routing function to determine the next node after main_router.
    Returns the name of the next node based on the task_name in state.
    """
    task_name = state.get("task_name")

    if task_name == "Handwriting":
        return "handwriting"
    elif task_name == "Vocabulary":
        return "vocabulary"
    elif task_name == "Idea Generation":
        return "idea_generation"
    elif task_name == "__CLARIFY__":
        # Route to clarification node
        return "clarification"
    else:
        # Fallback - should not happen
        return "clarification"
