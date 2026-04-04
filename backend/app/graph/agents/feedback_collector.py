"""
Feedback Collector Agent - ReAct agent for collecting optional user feedback.

Uses create_agent from langchain.agents for structured feedback parsing.
Runs after any generator calls finalize_lesson(). Parses user feedback
into structured data (category, rating, text) via tool calls.
"""

from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model


# --- System Prompt ---

FEEDBACK_COLLECTOR_PROMPT = """You are a feedback collector for an educational lesson planning platform.

The user just finished generating a lesson. Your job is to ask for optional
feedback and process their response.

## Rules

1. Ask ONE brief question: "Before we wrap up, do you have any feedback
   about the lesson or the platform? You can also say 'skip' to finish."

2. If the user provides feedback, call submit_feedback with:
   - category: "lesson" (about the generated content), "platform" (about
     the app/UX), or "general" (mixed or unclear)
   - rating: Extract a 1-5 rating if the user mentions one. Examples:
     "5 stars" → 5, "8/10" → 4, "terrible" → 1. If no rating mentioned,
     use 0 to indicate no rating.
   - text: The user's feedback in their own words

3. If the user says "skip", "no", "I'm good", "no thanks", etc.,
   call skip_feedback

4. Be brief. Don't ask follow-up questions after the initial ask.
"""


# --- Tool Definitions ---


@tool
def submit_feedback(category: str, rating: int, text: str) -> str:
    """
    Submit structured feedback from the user.

    Call this when the user provides feedback about the lesson or platform.

    Args:
        category: "lesson" (about generated content), "platform" (about the app/UX),
                  or "general" (mixed or unclear)
        rating: 1-5 rating if mentioned by user, 0 if no rating given
        text: The user's feedback in their own words
    """
    return "Thank you for your feedback! It has been recorded."


@tool
def skip_feedback() -> str:
    """
    Skip feedback collection.

    Call this when the user declines to provide feedback
    (says "skip", "no", "I'm good", "no thanks", etc.)
    """
    return "No problem! Thanks for using the platform."


# Tool lists and names for state extraction
FEEDBACK_TOOLS = [submit_feedback, skip_feedback]
SUBMIT_FEEDBACK_TOOL_NAME = "submit_feedback"
SKIP_FEEDBACK_TOOL_NAME = "skip_feedback"


def create_feedback_collector_agent(recursion_limit: int = 10):
    """
    Create the feedback collector ReAct agent.

    Args:
        recursion_limit: Maximum number of agent turns

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    model = get_chat_model("gpt-5.4-nano")

    agent = create_agent(
        model=model,
        tools=FEEDBACK_TOOLS,
        system_prompt=FEEDBACK_COLLECTOR_PROMPT,
    )

    return agent
