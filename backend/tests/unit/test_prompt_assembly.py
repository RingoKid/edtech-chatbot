"""
Unit tests for generator prompt assembly.

Validates that the prompt builder correctly filters reference materials
and injects only relevant content (target letter cues, target sound
gesture, selected activity descriptions, pre-selected standards).

No LLM calls — tests the prompt string itself.
"""

import re
from pathlib import Path
from typing import TypedDict

import pytest

# Path to reference materials
REFERENCE_DIR = Path(__file__).parent.parent.parent / "prompt" / "reference_materials"
HANDWRITING_DIR = REFERENCE_DIR / "handwriting"

# These imports will exist after implementation
# from app.graph.agents.handwriting_generator import get_handwriting_generator_prompt
# from app.graph.state import ActivityPlan

# ---------------------------------------------------------------------------
# Temporary inline type
# ---------------------------------------------------------------------------

class ActivityPlan(TypedDict):
    review: str
    sound_target: str
    handwriting: str
    handwriting_chain: str | None
    spelling: str
    standards: list[str]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_plan():
    """A valid K on-level plan for letter B."""
    return ActivityPlan(
        review="sound_spark",
        sound_target="sound_hunt",
        handwriting="trace_and_say",
        handwriting_chain=None,
        spelling="sound_letter_hunt",
        standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
    )


@pytest.fixture(scope="module")
def sample_plan_with_chain():
    """A valid PreK struggling plan with handwriting chain."""
    return ActivityPlan(
        review="sound_echo",
        sound_target="sound_check",
        handwriting="skywrite",
        handwriting_chain="trace_and_say",
        spelling="trace_the_sound",
        standards=["CLL6.4c", "CLL7.4a", "CLL9.4d"],
    )


# ---------------------------------------------------------------------------
# NOTE: These tests will call get_handwriting_generator_prompt() once it's
# implemented. For now they define the expected behavior.
#
# The implementation must satisfy:
# 1. Prompt contains only target letter's verbal cues (from Form F)
# 2. Prompt contains only target sound's gesture (from Form G)
# 3. Prompt contains descriptions for selected activities only
# 4. Prompt does NOT contain Form D content
# 5. Prompt does NOT contain Form H on initial generation
# 6. Prompt contains Forms A, B, C (grade-specific), E (universal)
# 7. Prompt contains previously_learned sounds as explicit list
# 8. Prompt contains pre-selected standards
# ---------------------------------------------------------------------------


class TestPromptFiltering:
    """Test that the prompt assembly correctly filters reference materials."""

    @pytest.fixture(autouse=True)
    def _skip_until_implemented(self):
        """Skip these tests until get_handwriting_generator_prompt is updated."""
        pytest.skip("Prompt assembly not yet implemented — contract tests only")

    def test_contains_only_target_letter_cues(self, sample_plan):
        """Only letter B cues should appear, not other letters."""
        # prompt = get_handwriting_generator_prompt(
        #     grade="K", letter="B", student_level="on-level",
        #     previously_learned=["m", "a", "s", "t"],
        #     skill_focus="isolating_sounds",
        #     activity_plan=sample_plan,
        # )
        prompt = ""  # placeholder

        # Target letter present
        assert "B \u2013 Big line down, rainbow bump, rainbow bump" in prompt
        assert "b \u2013 Big line down, rainbow bump from the middle" in prompt

        # Other letters absent
        assert "A \u2013 Big line up" not in prompt
        assert "Z \u2013 Little line across" not in prompt
        assert "C \u2013 Start at the top" not in prompt

    def test_contains_only_target_sound_gesture(self, sample_plan):
        """Only /b/ gesture should appear, not other sounds."""
        prompt = ""  # placeholder

        assert "/b/" in prompt
        assert "Bounce a ball" in prompt

        # Other gestures absent
        assert "/z/" not in prompt
        assert "buzzing bee" not in prompt

    def test_contains_selected_activity_descriptions(self, sample_plan):
        """Full descriptions for selected activities should be present."""
        prompt = ""  # placeholder

        # Sound Spark (review activity)
        assert "chorally pronounce the sound" in prompt
        # Sound Hunt (sound target activity)
        assert "beginning, middle, or ending sound" in prompt
        # Trace & Say (handwriting activity)
        assert "dotted-line handwriting templates" in prompt
        # Sound-Letter Hunt (spelling activity)
        assert "write the corresponding letter" in prompt

    def test_excludes_non_selected_activities(self, sample_plan):
        """Activities NOT in the plan should not have descriptions in prompt."""
        prompt = ""  # placeholder

        # Finger Run — not selected
        assert "run their finger from left to right across the handwriting lines" not in prompt
        # Spell Sprint — not selected
        assert "countdown to the next word" not in prompt
        # Chop the Sound — not selected
        assert 'remove (or "chop")' not in prompt

    def test_excludes_form_d(self, sample_plan):
        """Form D content should not be in the prompt."""
        prompt = ""  # placeholder

        assert "FORM D" not in prompt
        assert "form-d-scaffolded-activities" not in prompt
        assert "(low-level)" not in prompt
        assert "(middle-level)" not in prompt
        assert "(high-level)" not in prompt

    def test_excludes_form_h_on_initial_generation(self, sample_plan):
        """Form H should not be present during initial lesson generation."""
        prompt = ""  # placeholder

        assert "FORM H" not in prompt
        assert "Modification of Activity Examples" not in prompt

    def test_contains_universal_forms(self, sample_plan):
        """Forms A, B, and E should always be present."""
        prompt = ""  # placeholder

        # Form A — objectives verb list
        assert "Orient, Point, Match, Name" in prompt
        # Form B — lesson structure
        assert "Review & Connect" in prompt
        assert "Model, Explain & Engage" in prompt
        # Form E — best practices
        assert "evidence-based" in prompt.lower() or "proper way to hold a pencil" in prompt

    def test_contains_grade_specific_form_c(self, sample_plan):
        """Form C for the target grade should be present."""
        prompt = ""  # placeholder

        # K Form C example is about letter B
        assert "FORM C" in prompt or "form-c" in prompt.lower() or "Example" in prompt

    def test_contains_previously_learned_sounds(self, sample_plan):
        """Previously learned sounds must appear as explicit list."""
        prompt = ""  # placeholder

        assert "m" in prompt
        assert "a" in prompt
        assert "s" in prompt
        assert "t" in prompt

    def test_contains_pre_selected_standards(self, sample_plan):
        """Standards from the plan should be in the prompt."""
        prompt = ""  # placeholder

        for code in sample_plan["standards"]:
            assert code in prompt

    def test_handwriting_chain_included_when_present(self, sample_plan_with_chain):
        """If handwriting_chain is set, its description should be in prompt."""
        prompt = ""  # placeholder

        # SkyWrite (primary handwriting)
        assert "write letters in the air" in prompt
        # Trace & Say (chain activity)
        assert "dotted-line handwriting templates" in prompt


class TestPromptParameters:
    """Test that prompt parameters are correctly substituted."""

    @pytest.fixture(autouse=True)
    def _skip_until_implemented(self):
        pytest.skip("Prompt assembly not yet implemented — contract tests only")

    def test_grade_appears_in_prompt(self):
        prompt = ""  # placeholder
        assert "K" in prompt or "Kindergarten" in prompt

    def test_letter_appears_in_prompt(self):
        prompt = ""  # placeholder
        assert "B" in prompt

    def test_student_level_appears_in_prompt(self):
        prompt = ""  # placeholder
        assert "on-level" in prompt

    def test_skill_focus_appears_in_prompt(self):
        prompt = ""  # placeholder
        assert "isolating_sounds" in prompt or "isolating sounds" in prompt
