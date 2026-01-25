"""
Parameter Collection Agent - ReAct agent for collecting task-specific parameters.

Uses create_agent from langchain.agents for natural conversation flow.
The agent uses task-specific tools to submit collected parameters.
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.langfuse.client import get_langfuse_client
from app.graph.state import GraphState, GradeLevel, StudentLevel


# Default prompt used when Langfuse is unavailable or prompt doesn't exist
DEFAULT_PARAM_PROMPT = """You are a friendly lesson planning assistant helping a preschool teacher create a handwriting lesson.

Your job is to collect the necessary information to create a personalized handwriting lesson:
1. **Grade level** (required): PreK, K, or 1st
2. **Letter** (required): Which letter to practice (A-Z)
3. **Student level** (optional): struggling, on-level, or advanced (defaults to on-level)

IMPORTANT RULES:
- If the user already provided some information in the conversation, don't ask for it again
- Only ask for information that is still missing
- When you have grade and letter, call submit_handwriting_params immediately
- If grade is invalid (not PreK, K, or 1st), politely explain the valid options
- Letter should be a single letter A-Z (case insensitive)

Examples:
- User said "PreK letter A" → You have everything, call submit_handwriting_params(grade="PreK", letter="A", student_level="on-level")
- User said "letter B for kindergarten, struggling students" → Call submit_handwriting_params(grade="K", letter="B", student_level="struggling")
- User said "handwriting lesson" → Ask: "Which letter would you like to focus on, and what grade level (PreK, K, or 1st)?"
- User said "letter C" but no grade → Ask: "What grade level? PreK, K, or 1st?"

Be concise and friendly. Don't over-explain.
"""


# Langfuse configuration for prompt management
LANGFUSE_PROMPT_NAME = "param-agent"
LANGFUSE_PROMPT_LABEL = "production"


def get_param_prompt() -> str:
    """
    Fetch the param agent prompt from Langfuse.

    Falls back to DEFAULT_PARAM_PROMPT if:
    - Langfuse is not configured
    - Prompt doesn't exist in Langfuse
    - Any error occurs during fetch

    Returns:
        str: The system prompt for the param agent
    """
    client = get_langfuse_client()

    if client is None:
        return DEFAULT_PARAM_PROMPT

    try:
        prompt = client.get_prompt(LANGFUSE_PROMPT_NAME, label=LANGFUSE_PROMPT_LABEL)
        # For text prompts, compile() returns the prompt string
        return prompt.compile()
    except Exception:
        # Prompt not found or other error - use default
        return DEFAULT_PARAM_PROMPT


# --- Pydantic model for tool input validation ---


class SubmitHandwritingParams(BaseModel):
    """Schema for handwriting parameter submission."""
    grade: Literal["PreK", "K", "1st"] = Field(
        description="Grade level: PreK, K, or 1st"
    )
    letter: str = Field(
        description="The letter to practice (A-Z, case insensitive)"
    )
    student_level: Literal["struggling", "on-level", "advanced"] = Field(
        default="on-level",
        description="Student ability level for differentiation"
    )


# --- Parameter Collection Tool ---


@tool(args_schema=SubmitHandwritingParams)
def submit_handwriting_params(
    grade: Literal["PreK", "K", "1st"],
    letter: str,
    student_level: Literal["struggling", "on-level", "advanced"] = "on-level",
) -> str:
    """
    Submit the collected handwriting lesson parameters.

    Call this tool when you have collected:
    - grade: The grade level (PreK, K, or 1st)
    - letter: The letter to practice (A-Z)
    - student_level: Optional, defaults to "on-level"

    This signals that parameter collection is complete and the lesson
    can be generated.
    """
    # Normalize letter to uppercase
    letter_upper = letter.upper().strip()

    return (
        f"Parameters submitted: grade={grade}, letter={letter_upper}, "
        f"student_level={student_level}. Proceeding to lesson generation."
    )


# All param collection tools
PARAM_TOOLS = [submit_handwriting_params]

# Tool name for extraction
HANDWRITING_TOOL_NAME = "submit_handwriting_params"


def create_param_agent(recursion_limit: int = 10):
    """
    Create the parameter collection ReAct agent.

    Args:
        recursion_limit: Maximum number of agent turns (prevents infinite loops)

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    # Get model from registry
    model = get_chat_model("gpt-4o")

    # Get prompt from Langfuse (or default)
    system_prompt = get_param_prompt()

    # Create ReAct agent with tools
    agent = create_agent(
        model=model,
        tools=PARAM_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
