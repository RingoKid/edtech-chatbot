from langchain_core.messages import AIMessage, SystemMessage  # type: ignore[import-not-found]
from app.graph.state import GraphState
from app.schemas.task_route import TaskRoute
from app.graph.context import Context


ALLOWED_TASKS = {"Handwriting", "Vocabulary", "Idea Generation"}
TASK_KEYWORDS = {
    "Handwriting": ("handwriting", "write", "writing", "penmanship", "letters"),
    "Vocabulary": ("vocabulary", "words", "spelling", "definitions", "lexicon"),
    "Idea Generation": ("idea", "brainstorm", "creative", "plan", "story"),
}


def greeting_node(state: GraphState) -> dict:
    """
    Greets the user and presents the main task options.
    """
    welcome_message = AIMessage(
        content="Welcome! I'm here to help you build lesson plans. \n\nWhat would you like to work on?\n- Handwriting\n- Vocabulary\n- Idea Generation"
    )
    return {"messages": [welcome_message]}


def main_router(state: GraphState) -> dict:
    """
    Routes the user's choice to the appropriate task node.
    Uses structured output with Pydantic to classify the user's intent.
    """
    # Get the context and LLM with structured output
    context = Context()
    llm = context.model
    structured_llm = llm.with_structured_output(TaskRoute, strict=True)

    # Get the last message (user's choice)
    last_message = state["messages"][-1]
    user_text = last_message.content.lower()

    # Fast keyword routing for determinism without invoking the LLM
    for task, keywords in TASK_KEYWORDS.items():
        if any(keyword in user_text for keyword in keywords):
            print(f"DEBUG: Keyword routed to {task}")
            return {"task_name": task}

    # Create a system message to guide the classification
    system_prompt = SystemMessage(
        content="You are a routing assistant. The user must choose one of: Handwriting, Vocabulary, or Idea Generation. Classify their response into exactly one of these three options based on their intent."
    )

    try:
        # Invoke the LLM with structured output, including system prompt
        route = structured_llm.invoke([system_prompt, last_message])
        task_name = route.task_name if getattr(route, "task_name", None) in ALLOWED_TASKS else None

        if not task_name:
            raise ValueError(f"Unexpected task classification: {getattr(route, 'task_name', None)}")

        # On success, update task_name
        print(f"DEBUG: Successfully routed to {task_name}")
        return {"task_name": task_name}
    except Exception as e:
        # On failure (e.g., invalid choice like "spanish")
        print(f"DEBUG: Routing failed with error: {e}")
        error_message = AIMessage(
            content="I'm sorry, I didn't understand that choice. Can you please pick from Handwriting, Vocabulary, or Idea Generation?"
        )
        return {"messages": [error_message], "task_name": "__ERROR__"}


def stub_handwriting_node(state: GraphState) -> dict:
    """
    Placeholder for the Handwriting feature.
    """
    stub_message = AIMessage(content="*Handwriting feature coming soon!*")
    return {"messages": [stub_message]}


def stub_vocabulary_node(state: GraphState) -> dict:
    """
    Placeholder for the Vocabulary feature.
    """
    stub_message = AIMessage(content="*Vocabulary feature coming soon!*")
    return {"messages": [stub_message]}


def stub_idea_generation_node(state: GraphState) -> dict:
    """
    Placeholder for the Idea Generation feature.
    """
    stub_message = AIMessage(content="*Idea Generation feature coming soon!*")
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
    else:
        # If __ERROR__ or None, loop back to greeting
        return "greeting_node"

