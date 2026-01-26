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
from app.graph.state import (
    GraphState,
    GradeLevel,
    StudentLevel,
    WritingType,
    Genre,
    WritingStage,
)


# Default prompt used when Langfuse is unavailable or prompt doesn't exist
# NOTE: This prompt is generic - it tells the agent to look at conversation context
# to determine the task type and use the appropriate tool.
DEFAULT_PARAM_PROMPT = """You are a friendly lesson planning assistant for preschool teachers.

The user has been routed to you to collect parameters for their lesson.
Look at the conversation history to understand what type of lesson they want,
then use the appropriate tool to submit the collected parameters.

RULES:
1. Look at the routing context in the conversation to know the lesson type
2. Only ask for information that is still missing
3. Call the appropriate submit tool when you have all required parameters
4. Be concise and friendly - don't over-explain
5. Ask for one or two pieces of information at a time, not all at once

GRADE LEVELS (for all lesson types):
- PreK, K, or 1st only
- If user says an invalid grade, politely explain the valid options

STUDENT LEVEL (optional for all lesson types):
- struggling, on-level, or advanced
- Defaults to "on-level" if not specified - don't ask unless mentioned

AVAILABLE TOOLS:

1. submit_handwriting_params: For handwriting/letter formation lessons
   Required: grade (PreK/K/1st), letter (A-Z)
   Optional: student_level (defaults to on-level)

2. submit_vocabulary_params: For vocabulary & sentence structure lessons
   Required:
   - grade (PreK/K/1st)
   - writing_type (informational, narrative, personal_narrative, opinion)
   - key_vocabulary (list of vocabulary words)
   - objectives (teacher's focus, e.g., "be-verbs", "prepositional phrases")
   Optional: student_level (defaults to on-level)

3. submit_idea_generation_params: For idea generation & organization lessons
   Required:
   - grade (PreK/K/1st)
   - genre (narrative, informational, opinion)
   - genre_component (specific focus, e.g., "relevant details", "topic sentence")
   - writing_stage (brainstorm, initial_draft, revise, edit)
   - objectives (teacher's objective focus)
   Optional: student_level (defaults to on-level)

COLLECTION TIPS:
- For vocabulary lessons, ask about the writing unit type and key vocabulary words
- For idea generation, ask about the genre, what component they're focusing on, and what stage of writing
- Always confirm the grade level if not clear from context
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


class SubmitVocabularyParams(BaseModel):
    """Schema for vocabulary & sentence structure parameter submission."""
    grade: Literal["PreK", "K", "1st"] = Field(
        description="Grade level: PreK, K, or 1st"
    )
    writing_type: Literal["informational", "narrative", "personal_narrative", "opinion"] = Field(
        description="Type of writing unit: informational, narrative, personal_narrative, or opinion"
    )
    key_vocabulary: list[str] = Field(
        description="List of vocabulary words the teacher is working on"
    )
    objectives: str = Field(
        description="Teacher's objective focus (e.g., 'be-verbs', 'prepositional phrases')"
    )
    student_level: Literal["struggling", "on-level", "advanced"] = Field(
        default="on-level",
        description="Student ability level for differentiation"
    )


class SubmitIdeaGenerationParams(BaseModel):
    """Schema for idea generation & organization parameter submission."""
    grade: Literal["PreK", "K", "1st"] = Field(
        description="Grade level: PreK, K, or 1st"
    )
    genre: Literal["narrative", "informational", "opinion"] = Field(
        description="Type of genre: narrative, informational, or opinion"
    )
    genre_component: str = Field(
        description="Specific component to focus on (e.g., 'relevant details', 'topic sentence')"
    )
    writing_stage: Literal["brainstorm", "initial_draft", "revise", "edit"] = Field(
        description="Current stage in writing process"
    )
    objectives: str = Field(
        description="Teacher's objective focus for this lesson"
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


@tool(args_schema=SubmitVocabularyParams)
def submit_vocabulary_params(
    grade: Literal["PreK", "K", "1st"],
    writing_type: Literal["informational", "narrative", "personal_narrative", "opinion"],
    key_vocabulary: list[str],
    objectives: str,
    student_level: Literal["struggling", "on-level", "advanced"] = "on-level",
) -> str:
    """
    Submit the collected vocabulary & sentence structure lesson parameters.

    Call this tool when you have collected:
    - grade: The grade level (PreK, K, or 1st)
    - writing_type: Type of writing unit (informational, narrative, personal_narrative, opinion)
    - key_vocabulary: List of vocabulary words to focus on
    - objectives: Teacher's objective focus (e.g., "be-verbs", "prepositional phrases")
    - student_level: Optional, defaults to "on-level"

    This signals that parameter collection is complete and the lesson
    can be generated.
    """
    vocab_str = ", ".join(key_vocabulary)
    return (
        f"Parameters submitted: grade={grade}, writing_type={writing_type}, "
        f"vocabulary=[{vocab_str}], objectives={objectives}, "
        f"student_level={student_level}. Proceeding to lesson generation."
    )


@tool(args_schema=SubmitIdeaGenerationParams)
def submit_idea_generation_params(
    grade: Literal["PreK", "K", "1st"],
    genre: Literal["narrative", "informational", "opinion"],
    genre_component: str,
    writing_stage: Literal["brainstorm", "initial_draft", "revise", "edit"],
    objectives: str,
    student_level: Literal["struggling", "on-level", "advanced"] = "on-level",
) -> str:
    """
    Submit the collected idea generation & organization lesson parameters.

    Call this tool when you have collected:
    - grade: The grade level (PreK, K, or 1st)
    - genre: Type of genre (narrative, informational, opinion)
    - genre_component: Specific component to focus on (e.g., "relevant details", "topic sentence")
    - writing_stage: Current stage (brainstorm, initial_draft, revise, edit)
    - objectives: Teacher's objective focus
    - student_level: Optional, defaults to "on-level"

    This signals that parameter collection is complete and the lesson
    can be generated.
    """
    return (
        f"Parameters submitted: grade={grade}, genre={genre}, "
        f"component={genre_component}, stage={writing_stage}, "
        f"objectives={objectives}, student_level={student_level}. "
        f"Proceeding to lesson generation."
    )


# All param collection tools
PARAM_TOOLS = [
    submit_handwriting_params,
    submit_vocabulary_params,
    submit_idea_generation_params,
]

# Tool names for extraction
HANDWRITING_TOOL_NAME = "submit_handwriting_params"
VOCABULARY_TOOL_NAME = "submit_vocabulary_params"
IDEA_GENERATION_TOOL_NAME = "submit_idea_generation_params"


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
