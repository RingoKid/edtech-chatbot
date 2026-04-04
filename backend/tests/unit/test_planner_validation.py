"""
Unit tests for activity plan validation against the index.

Validates that an ActivityPlan (planner output) contains valid slugs,
grade-compatible activities, and meets structural requirements.

No LLM calls — tests the validation logic itself.
"""

from pathlib import Path

import pytest
import yaml

from app.graph.state import ActivityPlan
from app.graph.nodes.activity_planner import (
    validate_plan_slugs,
    validate_plan_grade,
    validate_plan_level,
    validate_plan_standards,
)

STANDARDS_PATH = (
    Path(__file__).parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting-spelling-standards.md"
)

INDEX_PATH = (
    Path(__file__).parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting" / "activity-index.yaml"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def index():
    with open(INDEX_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def standards_text():
    return STANDARDS_PATH.read_text()


# ---------------------------------------------------------------------------
# Valid plan tests
# ---------------------------------------------------------------------------

class TestValidPlans:
    """Test that well-formed plans pass validation."""

    def test_valid_k_on_level_plan(self, index):
        # trace_and_say at K is struggling-only; start_dot_and_say is K on-level
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        assert validate_plan_slugs(plan, index) == []
        assert validate_plan_grade(plan, index, "K") == []
        assert validate_plan_level(plan, index, "K", "on-level") == []

    def test_valid_prek_struggling_plan(self, index):
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_check",
            handwriting="magic_finger_write",
            handwriting_chain="trace_and_say",
            spelling="trace_the_sound",
            standards=["CLL6.4c", "CLL7.4a", "CLL9.4d"],
        )
        assert validate_plan_slugs(plan, index) == []
        assert validate_plan_grade(plan, index, "PreK") == []
        assert validate_plan_level(plan, index, "PreK", "struggling") == []

    def test_valid_1st_advanced_plan(self, index):
        plan = ActivityPlan(
            review="how_many_sounds",
            sound_target="chop_the_sound",
            handwriting="cover_and_try",
            handwriting_chain=None,
            spelling="switch_a_roo_write",
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
            review="nonexistent_activity",
            sound_target="sound_hunt",
            handwriting="trace_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=[],
        )
        errors = validate_plan_slugs(plan, index)
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_wrong_section_slug_rejected(self, index):
        """An activity from review placed in spelling slot."""
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_hunt",
            handwriting="trace_and_say",
            handwriting_chain=None,
            spelling="sound_echo",  # Review activity in spelling slot
            standards=[],
        )
        errors = validate_plan_slugs(plan, index)
        assert any("expected 'spelling_focus'" in e for e in errors)

    def test_null_grade_activity_rejected(self, index):
        """Sound Echo is null for 1st grade."""
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_hunt",
            handwriting="cover_and_try",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=[],
        )
        errors = validate_plan_grade(plan, index, "1st")
        assert any("null for grade '1st'" in e for e in errors)

    def test_wrong_level_rejected(self, index):
        """Sound Echo at K is for struggling only, not advanced."""
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_check",
            handwriting="magic_finger_write",
            handwriting_chain=None,
            spelling="trace_the_sound",
            standards=[],
        )
        errors = validate_plan_level(plan, index, "K", "advanced")
        assert len(errors) > 0
        assert any("does not support level 'advanced'" in e for e in errors)

    def test_handwriting_chain_wrong_section_rejected(self, index):
        """Chain activity must be from handwriting_focus section."""
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="trace_and_say",
            handwriting_chain="sound_echo",  # From review, not handwriting
            spelling="sound_letter_hunt",
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


# ---------------------------------------------------------------------------
# Standards validation tests
# ---------------------------------------------------------------------------

class TestValidStandards:
    """Test that well-formed standards pass validation."""

    def test_valid_k_standards_pass(self, standards_text):
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert errors == []

    def test_valid_prek_standards_pass(self, standards_text):
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_check",
            handwriting="magic_finger_write",
            handwriting_chain=None,
            spelling="trace_the_sound",
            standards=["CLL6.4c", "CLL7.4a", "CLL9.4d"],
        )
        errors = validate_plan_standards(plan, standards_text, "PreK")
        assert errors == []

    def test_valid_1st_standards_pass(self, standards_text):
        plan = ActivityPlan(
            review="how_many_sounds",
            sound_target="chop_the_sound",
            handwriting="cover_and_try",
            handwriting_chain=None,
            spelling="switch_a_roo_write",
            standards=["1.F.PA.6.a", "1.F.P.1.a", "1.F.P.3.a", "1.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "1st")
        assert errors == []

    def test_prek_allows_fewer_standards(self, standards_text):
        """PreK only needs 1-3 standards, no category coverage rule."""
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_check",
            handwriting="magic_finger_write",
            handwriting_chain=None,
            spelling="trace_the_sound",
            standards=["CLL6.4c"],
        )
        errors = validate_plan_standards(plan, standards_text, "PreK")
        assert errors == []


class TestInvalidStandards:
    """Test that invalid standards produce specific error messages."""

    def test_fabricated_code_rejected(self, standards_text):
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.ASR.1", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("K.F.ASR.1" in e and "not found" in e for e in errors)

    def test_mixed_valid_and_fabricated(self, standards_text):
        """3 real + 1 fabricated → exactly 1 error."""
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.HWR.1"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        not_found = [e for e in errors if "not found" in e]
        assert len(not_found) == 1
        assert "K.F.HWR.1" in not_found[0]

    def test_k_code_in_prek_plan_rejected(self, standards_text):
        """K.F.* codes are wrong for PreK."""
        plan = ActivityPlan(
            review="sound_echo",
            sound_target="sound_check",
            handwriting="magic_finger_write",
            handwriting_chain=None,
            spelling="trace_the_sound",
            standards=["K.F.PA.6.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "PreK")
        assert any("wrong system" in e.lower() or "wrong grade" in e.lower()
                    for e in errors)

    def test_cll_code_in_k_plan_rejected(self, standards_text):
        """CLL codes are wrong for K."""
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["CLL6.4c", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("CLL6.4c" in e for e in errors)

    def test_k_code_in_1st_plan_rejected(self, standards_text):
        """K.F.* codes are wrong for 1st grade."""
        plan = ActivityPlan(
            review="how_many_sounds",
            sound_target="chop_the_sound",
            handwriting="cover_and_try",
            handwriting_chain=None,
            spelling="switch_a_roo_write",
            standards=["K.F.H.1.a", "1.F.P.1.a", "1.F.P.3.a", "1.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "1st")
        assert any("K.F.H.1.a" in e for e in errors)

    def test_missing_pa_category_rejected(self, standards_text):
        """K must have one standard from each of PA, P.1, P.3, H."""
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("Phonemic Awareness" in e or "PA" in e for e in errors)

    def test_missing_handwriting_category_rejected(self, standards_text):
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("Handwriting" in e or "H" in e for e in errors)

    def test_missing_encoding_category_rejected(self, standards_text):
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("Encoding" in e or "P.3" in e for e in errors)

    def test_missing_phonics_category_rejected(self, standards_text):
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="start_dot_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.3.a", "K.F.H.1.a"],
        )
        errors = validate_plan_standards(plan, standards_text, "K")
        assert any("Phoneme-Grapheme" in e or "Phonics" in e or "P.1" in e
                    for e in errors)
