"""
Handwriting Generator Agent - ReAct agent for generating handwriting lessons.

Uses create_agent from langchain.agents for conversational lesson generation.
The agent generates lessons following the L4C methodology and can iterate
based on user feedback before finalizing.
"""

from pathlib import Path
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.langfuse.client import get_langfuse_client


# Path to reference materials
REFERENCE_MATERIALS_PATH = Path(__file__).parent.parent.parent.parent / "prompt" / "reference_materials" / "handwriting_reference.md"


# Default prompt used when Langfuse is unavailable or prompt doesn't exist
DEFAULT_HANDWRITING_GENERATOR_PROMPT = """You are a lesson planning expert specialized in handwriting and spelling instruction for early childhood education (PreK-1st grade).

You follow the L4C (Literacy for Children) methodology and the Science of Reading principles.

## Your Role

Generate complete, scripted handwriting and spelling lessons that teachers can use directly in their classrooms. Your lessons must be structured, detailed, and follow specific formatting conventions.

## Your Task

You have received the following parameters:
- **Grade Level**: {grade}
- **Target Letter**: {letter}
- **Student Level**: {student_level}

Generate a complete handwriting and spelling lesson following the structure in the reference materials.

## CRITICAL RULES

1. **Verbatim Explanations**: Each section's [Explanation] text MUST be copied EXACTLY from Form B in the reference materials. Do not paraphrase or modify these explanations.

2. **Verbal Cues**: The ##Sequence Verbal Cues for the target letter MUST match Form F exactly. Look up the correct verbal cues for letter "{letter}" in Form F.

3. **Activity Selection**: Based on student level "{student_level}":
   - struggling → Use LOW-LEVEL activities from Form D
   - on-level → Use MIDDLE-LEVEL activities from Form D
   - advanced → Use HIGH-LEVEL activities from Form D

4. **Notation Conventions** (MUST use these exactly):
   - [Explanation] → AI explains the parts of the lesson (use brackets)
   - #Teacher Script → What the teacher says (use single #)
   - (Child Response) → Expected student responses (use parentheses)
   - {{Teacher Does}} → Teacher actions (use curly braces)
   - +Gesture → Phoneme gesture (use plus sign)
   - ##Sequence Verbal Cues → Letter formation verbal cues (use ##)
   - *Modification → End-of-lesson prompt (use asterisk)

5. **Complete Structure**: Your output MUST include ALL of these sections:
   - A. Standards (1-3 Georgia Standards of Excellence)
   - B. Objectives (scaffolded objectives)
   - C. Materials (list of materials)
   - D. Scripted Lesson Plan:
     1. Review & Connect
     2. Model, Explain & Engage
     3. Guided Practice
     4. Application
     5. Wrap-Up

6. **End with Modification Prompt**: Always end with:
   *Adaptation: Let me know if you would like any modifications to the lesson

## After Generating

After presenting the lesson:
- If the user requests modifications, regenerate the lesson incorporating their feedback
- If the user approves the lesson (says "looks good", "thanks", "done", etc.), call the `finalize_lesson` tool

## Output Format

Generate the lesson in clean markdown format following Form C as your example.

---

## Reference Materials

{reference_materials}
"""


# Langfuse configuration for prompt management
LANGFUSE_PROMPT_NAME = "handwriting-generator"
LANGFUSE_PROMPT_LABEL = "production"


def load_reference_materials() -> str:
    """
    Load the handwriting reference materials from file.

    Returns:
        str: The contents of handwriting_reference.md
    """
    try:
        return REFERENCE_MATERIALS_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Reference materials not found. Please ensure handwriting_reference.md exists."


def get_handwriting_generator_prompt(
    grade: str,
    letter: str,
    student_level: str,
) -> str:
    """
    Fetch and compile the handwriting generator prompt.

    Combines:
    1. Langfuse prompt (or default if unavailable)
    2. Reference materials from local file
    3. Parameter substitution for grade, letter, student_level

    Args:
        grade: Grade level (PreK, K, 1st)
        letter: Target letter (A-Z)
        student_level: Student ability level (struggling, on-level, advanced)

    Returns:
        str: The complete system prompt with reference materials
    """
    client = get_langfuse_client()

    # Try to get prompt from Langfuse
    base_prompt = None
    if client is not None:
        try:
            prompt = client.get_prompt(LANGFUSE_PROMPT_NAME, label=LANGFUSE_PROMPT_LABEL)
            base_prompt = prompt.compile()
        except Exception:
            pass

    # Fall back to default if Langfuse unavailable
    if base_prompt is None:
        base_prompt = DEFAULT_HANDWRITING_GENERATOR_PROMPT

    # Load reference materials
    reference_materials = load_reference_materials()

    # Substitute parameters
    return base_prompt.format(
        grade=grade,
        letter=letter.upper(),
        student_level=student_level,
        reference_materials=reference_materials,
    )


# --- Tool Definition ---


@tool
def finalize_lesson() -> str:
    """
    Signal that the lesson is complete and the user is satisfied.

    Call this tool when:
    - User explicitly approves the lesson ("looks good", "perfect", etc.)
    - User says they're done or satisfied
    - User thanks you without requesting changes

    This will end the lesson generation conversation.
    """
    return "Lesson finalized. The lesson generation is complete."


# Tool list for the agent
GENERATOR_TOOLS = [finalize_lesson]

# Tool name for state extraction
FINALIZE_TOOL_NAME = "finalize_lesson"


def create_handwriting_generator_agent(
    grade: str,
    letter: str,
    student_level: str,
    recursion_limit: int = 10,
):
    """
    Create the handwriting generator ReAct agent.

    Args:
        grade: Grade level for the lesson
        letter: Target letter for the lesson
        student_level: Student ability level for differentiation
        recursion_limit: Maximum number of agent turns

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    # Get model from registry
    model = get_chat_model("gpt-4o")

    # Get prompt with parameters and reference materials
    system_prompt = get_handwriting_generator_prompt(
        grade=grade,
        letter=letter,
        student_level=student_level,
    )

    # Create ReAct agent with finalize tool
    agent = create_agent(
        model=model,
        tools=GENERATOR_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
