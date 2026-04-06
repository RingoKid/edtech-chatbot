"""
Activity Planner Agent - Selects appropriate activities for handwriting lessons.

Reads the activity index and student parameters to choose one activity
per lesson section (review, sound target, handwriting, spelling).
Returns a structured ActivityPlan with activity slugs and standards.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.graph.utils.extractors import extract_grade_standards

PLANNER_MODEL = "gpt-5.4-mini"

INDEX_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting" / "activity-index.yaml"
)

STANDARDS_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting-spelling-standards.md"
)

# Map grade parameter to section header in standards doc
GRADE_TO_STANDARDS_HEADER = {
    "PreK": "PreK",
    "K": "Kindergarten",
    "1st": "1st Grade",
}


DEFAULT_ACTIVITY_PLANNER_PROMPT = """You are an expert activity planner for early childhood handwriting and spelling lessons.

Your job: select ONE activity per lesson section that best fits the student parameters.

## Student Parameters

- **Grade**: {grade}
- **Target Letter**: {letter}
- **Student Level**: {student_level}
- **Previously Learned**: {previously_learned}
- **Skill Focus**: {skill_focus}

## Selection Rules

1. **Grade compatibility**: The activity's `by_grade.{grade}` must NOT be null.
2. **Level compatibility**: The student level "{student_level}" must appear in `by_grade.{grade}.levels`.
3. **Skill focus alignment**: Prefer activities whose `skill_focus` includes "{skill_focus}".
4. **Prerequisites**: Only select activities whose prerequisites are met by `previously_learned`. If `previously_learned` is empty, this is the student's first lesson — pick entry-level activities (rank 1-2).
5. **Difficulty rank**: Lower rank = easier. Match rank to readiness:
   - struggling → prefer rank 1-3
   - on-level → prefer rank 2-5
   - advanced → prefer rank 4+

## Sections to Fill

Select exactly ONE activity slug (the `id` field) for each:

1. **review** — from the `review` section
2. **sound_target** — from the `sound_target_focus` section
3. **handwriting** — from the `handwriting_focus` section
4. **spelling** — from the `spelling_focus` section

Optionally, you may also select:
5. **handwriting_chain** — a SECOND activity from `handwriting_focus` for a rehearsal→writing progression (e.g., SkyWrite then Trace & Say). Set to null if not needed.

## Standards

Select standards codes from the reference below. Use ONLY codes that appear in the reference — do NOT invent or guess codes.

- **PreK**: Select 1–3 GELDS codes (CLL prefix) from the reference.
- **K**: Select at least 4 codes (K.F.* format), one from EACH category: Phonemic Awareness (PA), Phoneme-Grapheme Correspondence (P.1), Encoding (P.3), Handwriting (H).
- **1st**: Select at least 4 codes (1.F.* format), same 4 categories as K.

### Standards Reference ({grade})

{grade_standards}

## Activity Index

{activity_index}

## Lesson Directives

In addition to selecting activities and standards, you must determine 6 lesson directives. These are pedagogical decisions that the generator will execute directly — it will NOT re-derive them.

### spelling_pattern
What word pattern should the lesson target?
- PreK → `single_sound`
- K → `CVC`
- 1st + vowel letter + on-level/advanced → `CVCe`
- 1st + vowel letter + struggling → `CVC`
- 1st + consonant letter → `CVC` or `CCVC`/`CVCC` depending on letter position patterns

Valid values: `single_sound`, `VC`, `CVC`, `CVCe`, `CCVC`, `CVCC`

### include_directionality
Should the lesson teach left-to-right movement and line placement (top/middle/bottom)?
- PreK → true
- K + struggling → true
- K + on-level/advanced → false
- 1st → false

### include_articulation
Should the lesson include mouth/lip/tongue/vocal box instruction for the target sound?
- PreK → true
- K → true
- 1st → false (students learned this in PreK/K)

### guided_practice_techniques
Ordered list of techniques for Section 3 (Guided Practice). Select from these slugs:
`magic_finger_write`, `trace_and_say`, `write_and_say`, `say_and_write`, `write_and_sound`, `disappearing_letter`, `cover_and_try`

Grade + level guidance:
- PreK → `[magic_finger_write, trace_and_say, write_and_say]`
- K + struggling → `[magic_finger_write, trace_and_say, write_and_say]`
- K + on-level → `[trace_and_say, say_and_write, write_and_say]`
- K + advanced → `[say_and_write, write_and_say, write_and_sound]`
- 1st + struggling → `[say_and_write, write_and_say, write_and_sound]`
- 1st + on-level → `[cover_and_try, say_and_write, write_and_sound]`
- 1st + advanced → `[cover_and_try, disappearing_letter, write_and_sound]`

### scaffolding_intensity
How much support does the student need?
- PreK → `heavy`
- K + struggling → `heavy`
- K + on-level/advanced → `moderate`
- 1st + struggling → `moderate`
- 1st + on-level/advanced → `light`

### content_scope
Write 2-3 sentences describing the lesson's pedagogical focus. Include:
- What sound positions to target (beginning, ending, medial)
- What the application task should require
- Specific pattern contrasts if applicable

Examples:
- PreK: "This lesson introduces the /m/ sound in isolation. Students will identify the /m/ sound at the beginning of words and practice writing the lowercase letter m. Application focuses on writing the single letter from memory."
- K: "This lesson teaches the letter B within CVC word context. Students identify /b/ at the beginning and ending of words like 'bat' and 'cab'. Application requires spelling complete CVC words containing the /b/ sound."
- 1st (vowel, on-level): "This lesson focuses on the long /ā/ sound through CVCe spelling patterns. Students MUST contrast CVC vs CVCe pairs (e.g., cap→cape, tap→tape, mat→mate) to understand how silent e changes the vowel sound. Application requires spelling CVCe words and explaining the pattern."

## Instructions

Analyze the index above, then call `submit_activity_plan` with your selections and directives. Use the `id` field (slug) for each activity, NOT the display name.
"""


class SubmitActivityPlan(BaseModel):
    """Schema for activity plan submission."""
    review: str = Field(
        description="Activity slug (id) from the review section"
    )
    sound_target: str = Field(
        description="Activity slug (id) from the sound_target_focus section"
    )
    handwriting: str = Field(
        description="Activity slug (id) from the handwriting_focus section"
    )
    handwriting_chain: Optional[str] = Field(
        default=None,
        description="Optional second handwriting activity slug for rehearsal→writing chain"
    )
    spelling: str = Field(
        description="Activity slug (id) from the spelling_focus section"
    )
    standards: list[str] = Field(
        description="Grade-appropriate standards codes"
    )
    # Lesson directives
    spelling_pattern: str = Field(
        description="Word pattern: single_sound, VC, CVC, CVCe, CCVC, or CVCC"
    )
    include_directionality: bool = Field(
        description="Whether to teach left-to-right and line placement"
    )
    include_articulation: bool = Field(
        description="Whether to include mouth/lip/tongue instruction"
    )
    guided_practice_techniques: list[str] = Field(
        description="Ordered technique slugs for Section 3 Guided Practice"
    )
    scaffolding_intensity: str = Field(
        description="heavy, moderate, or light"
    )
    content_scope: str = Field(
        description="2-3 sentence description of the lesson's pedagogical focus"
    )


@tool(args_schema=SubmitActivityPlan)
def submit_activity_plan(
    review: str,
    sound_target: str,
    handwriting: str,
    spelling: str,
    standards: list[str],
    spelling_pattern: str,
    include_directionality: bool,
    include_articulation: bool,
    guided_practice_techniques: list[str],
    scaffolding_intensity: str,
    content_scope: str,
    handwriting_chain: Optional[str] = None,
) -> str:
    """
    Submit the selected activity plan with lesson directives.

    Call this tool after analyzing the activity index and selecting
    one activity per section that fits the student parameters.
    Use the id (slug) field, not the display name.
    """
    return (
        f"Activity plan submitted: review={review}, sound_target={sound_target}, "
        f"handwriting={handwriting}, handwriting_chain={handwriting_chain}, "
        f"spelling={spelling}, standards={standards}, "
        f"spelling_pattern={spelling_pattern}, scaffolding={scaffolding_intensity}. "
        f"Proceeding to lesson generation."
    )


PLANNER_TOOLS = [submit_activity_plan]
PLANNER_TOOL_NAME = "submit_activity_plan"


def load_activity_index() -> str:
    """Load the activity index YAML as a string for the planner prompt."""
    try:
        return INDEX_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Activity index not found."


def load_grade_standards(grade: str) -> str:
    """Load grade-filtered standards section for the planner prompt."""
    try:
        standards_text = STANDARDS_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Standards reference not found."

    header = GRADE_TO_STANDARDS_HEADER.get(grade, grade)
    section = extract_grade_standards(standards_text, header)
    return section if section else f"No standards found for grade '{grade}'."


def get_activity_planner_prompt(
    grade: str,
    letter: str,
    student_level: str,
    previously_learned: list[str],
    skill_focus: str,
) -> str:
    """Compile the activity planner prompt with parameters, index, and standards."""
    activity_index = load_activity_index()
    grade_standards = load_grade_standards(grade)
    learned_str = ", ".join(previously_learned) if previously_learned else "(none — first lesson)"

    return DEFAULT_ACTIVITY_PLANNER_PROMPT.format(
        grade=grade,
        letter=letter,
        student_level=student_level,
        previously_learned=learned_str,
        skill_focus=skill_focus,
        activity_index=activity_index,
        grade_standards=grade_standards,
    )


def create_activity_planner_agent(
    grade: str,
    letter: str,
    student_level: str,
    previously_learned: list[str],
    skill_focus: str,
    recursion_limit: int = 10,
):
    """
    Create the activity planner ReAct agent.

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    model = get_chat_model(PLANNER_MODEL)

    system_prompt = get_activity_planner_prompt(
        grade=grade,
        letter=letter,
        student_level=student_level,
        previously_learned=previously_learned,
        skill_focus=skill_focus,
    )

    agent = create_agent(
        model=model,
        tools=PLANNER_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
