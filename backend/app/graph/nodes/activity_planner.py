"""
Activity Planner Node - Graph node that runs the planner agent and validates output.

Extracts the ActivityPlan from the planner's tool call, validates it against
the activity index, and retries with error feedback if validation fails.
"""

import logging
from pathlib import Path

import yaml
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)

from app.graph.state import GraphState, ActivityPlan
from app.graph.agents.activity_planner import (
    create_activity_planner_agent,
    PLANNER_TOOL_NAME,
)
from app.graph.utils.extractors import extract_standard

INDEX_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting" / "activity-index.yaml"
)

STANDARDS_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting-spelling-standards.md"
)

SECTION_TO_INDEX_KEY = {
    "review": "review",
    "sound_target": "sound_target_focus",
    "handwriting": "handwriting_focus",
    "handwriting_chain": "handwriting_focus",
    "spelling": "spelling_focus",
}

MAX_RETRIES = 2


def _load_index() -> dict:
    """Load and parse the activity index YAML."""
    with open(INDEX_PATH) as f:
        return yaml.safe_load(f)


def _build_id_lookup(index: dict) -> dict[str, tuple[str, dict]]:
    """Build slug→(section_key, activity) lookup from index."""
    lookup: dict[str, tuple[str, dict]] = {}
    for section_key, section in index["sections"].items():
        for activity in section["activities"]:
            lookup[activity["id"]] = (section_key, activity)
    return lookup


def validate_plan_slugs(plan: ActivityPlan, index: dict) -> list[str]:
    """
    Validate that all activity slugs exist and belong to correct sections.

    Returns list of error messages (empty = valid).
    """
    errors = []
    id_lookup = _build_id_lookup(index)

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        expected_section = SECTION_TO_INDEX_KEY[field]

        if slug not in id_lookup:
            errors.append(f"{field}: slug '{slug}' not found in index")
        elif id_lookup[slug][0] != expected_section:
            errors.append(
                f"{field}: slug '{slug}' belongs to section "
                f"'{id_lookup[slug][0]}', expected '{expected_section}'"
            )

    if plan.get("handwriting_chain"):
        chain_slug = plan["handwriting_chain"]
        if chain_slug not in id_lookup:
            errors.append(f"handwriting_chain: slug '{chain_slug}' not found")
        elif id_lookup[chain_slug][0] != "handwriting_focus":
            errors.append(
                f"handwriting_chain: slug '{chain_slug}' not in handwriting_focus"
            )

    return errors


def validate_plan_grade(plan: ActivityPlan, index: dict, grade: str) -> list[str]:
    """
    Validate that all activities are available for the given grade.

    Returns list of error messages (empty = valid).
    """
    errors = []
    id_lookup = _build_id_lookup(index)

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        if slug not in id_lookup:
            continue
        activity = id_lookup[slug][1]
        grade_config = activity["by_grade"].get(grade)
        if grade_config is None:
            errors.append(
                f"{field}: activity '{slug}' is null for grade '{grade}'"
            )

    if plan.get("handwriting_chain"):
        chain_slug = plan["handwriting_chain"]
        if chain_slug in id_lookup:
            activity = id_lookup[chain_slug][1]
            grade_config = activity["by_grade"].get(grade)
            if grade_config is None:
                errors.append(
                    f"handwriting_chain: activity '{chain_slug}' is null "
                    f"for grade '{grade}'"
                )

    return errors


def validate_plan_level(
    plan: ActivityPlan, index: dict, grade: str, student_level: str,
) -> list[str]:
    """
    Validate that all activities support the student level at the given grade.

    Returns list of error messages (empty = valid).
    """
    errors = []
    id_lookup = _build_id_lookup(index)

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        if slug not in id_lookup:
            continue
        activity = id_lookup[slug][1]
        grade_config = activity["by_grade"].get(grade)
        if grade_config is None:
            continue
        if student_level not in grade_config["levels"]:
            errors.append(
                f"{field}: activity '{slug}' at grade '{grade}' does not "
                f"support level '{student_level}' "
                f"(supports: {grade_config['levels']})"
            )

    return errors


# Grade → expected code prefix
GRADE_TO_CODE_PREFIX = {
    "PreK": "CLL",
    "K": "K.F.",
    "1st": "1.F.",
}

# Required categories for K and 1st (prefix after grade prefix)
REQUIRED_CATEGORIES = {
    "Phonemic Awareness (PA)": "PA",
    "Phoneme-Grapheme Correspondence (P.1)": "P.1",
    "Encoding (P.3)": "P.3",
    "Handwriting (H)": "H",
}


def validate_plan_standards(
    plan: ActivityPlan, standards_text: str, grade: str,
) -> list[str]:
    """
    Validate that the planner's selected standards are real and appropriate.

    Checks:
    1. Each code exists in the reference file
    2. Each code uses the correct grade prefix
    3. K and 1st must cover 4 required categories
    4. Non-empty list required for all grades

    Returns list of error messages (empty = valid).
    """
    errors = []
    codes = plan.get("standards", [])

    if not codes:
        errors.append("standards: list is empty — at least 1 standard required")
        return errors

    expected_prefix = GRADE_TO_CODE_PREFIX.get(grade, "")

    for code in codes:
        # Check grade system
        if not code.startswith(expected_prefix):
            errors.append(
                f"standards: '{code}' has wrong grade prefix for {grade} "
                f"(expected '{expected_prefix}*')"
            )
            continue

        # Check existence in reference
        if not extract_standard(standards_text, code):
            errors.append(f"standards: '{code}' not found in reference")

    # Category coverage for K and 1st
    if grade in ("K", "1st"):
        grade_prefix = GRADE_TO_CODE_PREFIX[grade]
        for category_name, category_suffix in REQUIRED_CATEGORIES.items():
            cat_prefix = f"{grade_prefix}{category_suffix}"
            if not any(c.startswith(cat_prefix) for c in codes):
                errors.append(
                    f"standards: missing required category {category_name}"
                )

    return errors


def _extract_plan(messages: list) -> ActivityPlan | None:
    """Extract ActivityPlan from planner tool call in messages."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == PLANNER_TOOL_NAME:
                    args = tool_call.get('args', {})
                    return ActivityPlan(
                        review=args.get('review', ''),
                        sound_target=args.get('sound_target', ''),
                        handwriting=args.get('handwriting', ''),
                        handwriting_chain=args.get('handwriting_chain'),
                        spelling=args.get('spelling', ''),
                        standards=args.get('standards', []),
                    )
    return None


async def activity_planner_node(state: GraphState) -> dict:
    """
    Node that runs the activity planner and validates its output.

    Retries up to MAX_RETRIES times if validation fails.
    """
    params = state.get("handwriting_params")
    if params is None:
        return {
            "messages": [AIMessage(content="Error: No handwriting parameters found.")],
        }

    index = _load_index()

    # Load standards reference for validation
    try:
        standards_text = STANDARDS_PATH.read_text()
    except FileNotFoundError:
        standards_text = ""
        logger.warning("Standards reference file not found at %s", STANDARDS_PATH)

    agent = create_activity_planner_agent(
        grade=params["grade"],
        letter=params["letter"],
        student_level=params["student_level"],
        previously_learned=params.get("previously_learned", []),
        skill_focus=params.get("skill_focus", "isolating_sounds"),
    )

    messages = list(state["messages"])
    plan = None
    errors = []

    for attempt in range(1 + MAX_RETRIES):
        result = await agent.ainvoke({"messages": messages})
        new_messages = result.get("messages", [])

        plan = _extract_plan(new_messages)
        if plan is None:
            logger.warning(
                "Planner attempt %d/%d: no tool call found in response",
                attempt + 1, 1 + MAX_RETRIES,
            )
            messages = new_messages
            continue

        # Validate
        errors = (
            validate_plan_slugs(plan, index)
            + validate_plan_grade(plan, index, params["grade"])
            + validate_plan_level(plan, index, params["grade"], params["student_level"])
            + validate_plan_standards(plan, standards_text, params["grade"])
        )

        if not errors:
            return {
                "messages": new_messages,
                "activity_plan": plan,
            }

        if attempt < MAX_RETRIES:
            error_feedback = (
                "The activity plan has validation errors. Please fix and resubmit:\n"
                + "\n".join(f"- {e}" for e in errors)
            )
            messages = new_messages + [HumanMessage(content=error_feedback)]

    # Max retries exhausted
    if plan is not None:
        logger.warning(
            "Planner exhausted %d retries with validation errors, "
            "using last plan anyway: %s",
            MAX_RETRIES, errors,
        )
    else:
        logger.error(
            "Planner exhausted %d retries without producing a plan. "
            "Generator will run without activity plan.",
            MAX_RETRIES,
        )

    return {
        "messages": new_messages,
        "activity_plan": plan,
    }
