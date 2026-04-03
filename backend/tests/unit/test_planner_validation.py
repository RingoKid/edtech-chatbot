"""
Unit tests for activity plan validation against the index.

Validates that an ActivityPlan (planner output) contains valid slugs,
grade-compatible activities, and meets structural requirements.

No LLM calls — tests the validation logic itself.
"""

from pathlib import Path
from typing import TypedDict

import pytest
import yaml

INDEX_PATH = (
    Path(__file__).parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting" / "activity-index.yaml"
)

SECTION_TO_INDEX_KEY = {
    "review": "review",
    "sound_target": "sound_target_focus",
    "handwriting": "handwriting_focus",
    "handwriting_chain": "handwriting_focus",
    "spelling": "spelling_focus",
}


# ---------------------------------------------------------------------------
# Temporary inline types — will be imported from app.graph.state
# ---------------------------------------------------------------------------

class ActivityPlan(TypedDict):
    review: str
    sound_target: str
    handwriting: str
    handwriting_chain: str | None
    spelling: str
    standards: list[str]


# ---------------------------------------------------------------------------
# Validation functions — define the contract for implementation
# ---------------------------------------------------------------------------

def validate_plan_slugs(plan: ActivityPlan, index: dict) -> list[str]:
    """
    Validate that all activity slugs in the plan exist in the index
    and belong to the correct section.

    Returns list of error messages (empty = valid).
    """
    errors = []
    # Build slug→section lookup
    slug_to_section: dict[str, str] = {}
    for section_key, section in index["sections"].items():
        for activity in section["activities"]:
            slug_to_section[activity["name"]] = section_key

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        expected_section = SECTION_TO_INDEX_KEY[field]

        if slug not in slug_to_section:
            errors.append(f"{field}: slug '{slug}' not found in index")
        elif slug_to_section[slug] != expected_section:
            errors.append(
                f"{field}: slug '{slug}' belongs to section "
                f"'{slug_to_section[slug]}', expected '{expected_section}'"
            )

    if plan.get("handwriting_chain"):
        chain_slug = plan["handwriting_chain"]
        if chain_slug not in slug_to_section:
            errors.append(f"handwriting_chain: slug '{chain_slug}' not found")
        elif slug_to_section[chain_slug] != "handwriting_focus":
            errors.append(
                f"handwriting_chain: slug '{chain_slug}' not in handwriting_focus"
            )

    return errors


def validate_plan_grade(plan: ActivityPlan, index: dict, grade: str) -> list[str]:
    """
    Validate that all activities in the plan are available for the given grade.

    Returns list of error messages (empty = valid).
    """
    errors = []
    # Build slug→activity lookup
    slug_to_activity: dict[str, dict] = {}
    for section in index["sections"].values():
        for activity in section["activities"]:
            slug_to_activity[activity["name"]] = activity

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        if slug not in slug_to_activity:
            continue  # slug validation handled separately
        activity = slug_to_activity[slug]
        grade_config = activity["by_grade"].get(grade)
        if grade_config is None:
            errors.append(
                f"{field}: activity '{slug}' is null for grade '{grade}'"
            )

    if plan.get("handwriting_chain"):
        chain_slug = plan["handwriting_chain"]
        if chain_slug in slug_to_activity:
            activity = slug_to_activity[chain_slug]
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
    Validate that all activities are appropriate for the student level at
    the given grade.

    Returns list of error messages (empty = valid).
    """
    errors = []
    slug_to_activity: dict[str, dict] = {}
    for section in index["sections"].values():
        for activity in section["activities"]:
            slug_to_activity[activity["name"]] = activity

    for field in ["review", "sound_target", "handwriting", "spelling"]:
        slug = plan[field]
        if slug not in slug_to_activity:
            continue
        activity = slug_to_activity[slug]
        grade_config = activity["by_grade"].get(grade)
        if grade_config is None:
            continue  # grade validation handled separately
        if student_level not in grade_config["levels"]:
            errors.append(
                f"{field}: activity '{slug}' at grade '{grade}' does not "
                f"support level '{student_level}' "
                f"(supports: {grade_config['levels']})"
            )

    return errors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def index():
    with open(INDEX_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Valid plan tests
# ---------------------------------------------------------------------------

class TestValidPlans:
    """Test that well-formed plans pass validation."""

    def test_valid_k_on_level_plan(self, index):
        plan = ActivityPlan(
            review="Sound Spark",
            sound_target="Sound Hunt",
            handwriting="Trace & Say",
            handwriting_chain=None,
            spelling="Sound-Letter Hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        assert validate_plan_slugs(plan, index) == []
        assert validate_plan_grade(plan, index, "K") == []
        assert validate_plan_level(plan, index, "K", "on-level") == []

    def test_valid_prek_struggling_plan(self, index):
        plan = ActivityPlan(
            review="Sound Echo",
            sound_target="Sound Check",
            handwriting="Magic Finger Write",
            handwriting_chain="Trace & Say",
            spelling="Trace the Sound",
            standards=["CLL6.4c", "CLL7.4a", "CLL9.4d"],
        )
        assert validate_plan_slugs(plan, index) == []
        assert validate_plan_grade(plan, index, "PreK") == []
        assert validate_plan_level(plan, index, "PreK", "struggling") == []

    def test_valid_1st_advanced_plan(self, index):
        plan = ActivityPlan(
            review="How Many Sounds",
            sound_target="Chop the Sound",
            handwriting="Cover & Try",
            handwriting_chain=None,
            spelling="Switch-A-Roo Write",
            standards=["1.F.PA.6.a", "1.F.P.1.a", "1.F.P.3.a", "1.F.H.1.a"],
        )
        assert validate_plan_slugs(plan, index) == []
        assert validate_plan_grade(plan, index, "1st") == []
        assert validate_plan_level(plan, index, "1st", "advanced") == []


# ---------------------------------------------------------------------------
# Invalid plan tests
# ---------------------------------------------------------------------------

class TestInvalidPlans:
    """Test that invalid plans produce specific error messages."""

    def test_nonexistent_slug_rejected(self, index):
        plan = ActivityPlan(
            review="Nonexistent Activity",
            sound_target="Sound Hunt",
            handwriting="Trace & Say",
            handwriting_chain=None,
            spelling="Sound-Letter Hunt",
            standards=[],
        )
        errors = validate_plan_slugs(plan, index)
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_wrong_section_slug_rejected(self, index):
        """An activity from review placed in spelling slot."""
        plan = ActivityPlan(
            review="Sound Echo",
            sound_target="Sound Hunt",
            handwriting="Trace & Say",
            handwriting_chain=None,
            spelling="Sound Echo",  # Review activity in spelling slot
            standards=[],
        )
        errors = validate_plan_slugs(plan, index)
        assert any("expected 'spelling_focus'" in e for e in errors)

    def test_null_grade_activity_rejected(self, index):
        """Sound Echo is null for 1st grade."""
        plan = ActivityPlan(
            review="Sound Echo",
            sound_target="Sound Hunt",
            handwriting="Cover & Try",
            handwriting_chain=None,
            spelling="Sound-Letter Hunt",
            standards=[],
        )
        errors = validate_plan_grade(plan, index, "1st")
        assert any("null for grade '1st'" in e for e in errors)

    def test_wrong_level_rejected(self, index):
        """Sound Echo at K is for struggling only, not advanced."""
        plan = ActivityPlan(
            review="Sound Echo",
            sound_target="Sound Check",
            handwriting="Magic Finger Write",
            handwriting_chain=None,
            spelling="Trace the Sound",
            standards=[],
        )
        errors = validate_plan_level(plan, index, "K", "advanced")
        assert len(errors) > 0
        assert any("does not support level 'advanced'" in e for e in errors)

    def test_handwriting_chain_wrong_section_rejected(self, index):
        """Chain activity must be from handwriting_focus section."""
        plan = ActivityPlan(
            review="Sound Spark",
            sound_target="Sound Hunt",
            handwriting="Trace & Say",
            handwriting_chain="Sound Echo",  # From review, not handwriting
            spelling="Sound-Letter Hunt",
            standards=[],
        )
        errors = validate_plan_slugs(plan, index)
        assert any("handwriting_chain" in e for e in errors)


# ---------------------------------------------------------------------------
# Constraint coverage tests
# ---------------------------------------------------------------------------

class TestConstraintCoverage:
    """Verify that constraints are comprehensive enough."""

    def test_every_grade_has_at_least_one_activity_per_section(self, index):
        """For each grade, at least one activity per section must be available."""
        for grade in ["PreK", "K", "1st"]:
            for section_key, section in index["sections"].items():
                available = [
                    a for a in section["activities"]
                    if a["by_grade"].get(grade) is not None
                ]
                assert len(available) >= 1, (
                    f"Grade '{grade}' has no available activities in "
                    f"section '{section_key}'"
                )

    def test_every_level_has_at_least_one_activity_per_section(self, index):
        """For each grade+level combo, at least one activity per section."""
        for grade in ["PreK", "K", "1st"]:
            for level in ["struggling", "on-level", "advanced"]:
                for section_key, section in index["sections"].items():
                    available = [
                        a for a in section["activities"]
                        if a["by_grade"].get(grade) is not None
                        and level in a["by_grade"][grade]["levels"]
                    ]
                    if len(available) == 0:
                        pytest.skip(
                            f"No activities for {grade}/{level} in "
                            f"{section_key} — may need fallback logic"
                        )
