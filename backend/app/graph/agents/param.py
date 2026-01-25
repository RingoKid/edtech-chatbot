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
# NOTE: This prompt is generic - it tells the agent to look at conversation context
# to determine the task type and use the appropriate tool. Currently only handwriting
# is implemented; vocabulary and idea_generation tools will be added later.
DEFAULT_PARAM_PROMPT = """You are a friendly lesson planning assistant for preschool teachers.

The user has been routed to you to collect parameters for their lesson.
Look at the conversation history to understand what type of lesson they want,
then use the appropriate tool to submit the collected parameters.

RULES:
1. Look at the routing context in the conversation to know the lesson type
2. Only ask for information that is still missing
3. Call the appropriate submit tool when you have all required parameters
4. Be concise and friendly - don't over-explain

GRADE LEVELS (when applicable):
- PreK, K, or 1st only
- If user says an invalid grade, politely explain the valid options

CURRENTLY AVAILABLE TOOLS:
- submit_handwriting_params: For handwriting/letter formation lessons
  - Required: grade (PreK/K/1st), letter (A-Z)
  - Optional: student_level (struggling/on-level/advanced, defaults to on-level)

(Future tools: submit_vocabulary_params, submit_idea_params)
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
