"""
Unit tests for generator prompt assembly.

Validates that the prompt builder correctly filters reference materials
and injects only relevant content (target letter cues, target sound
gesture, selected activity descriptions, pre-selected standards).

No LLM calls — tests the prompt string itself.
"""

from pathlib import Path

import pytest

# Path to reference materials
REFERENCE_DIR = Path(__file__).parent.parent.parent / "prompt" / "reference_materials"
HANDWRITING_DIR = REFERENCE_DIR / "handwriting"

from app.graph.agents.handwriting_generator import get_handwriting_generator_prompt
from app.graph.state import ActivityPlan


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
        spelling_pattern="CVC",
        include_directionality=False,
        include_articulation=True,
        guided_practice_techniques=["trace_and_say", "say_and_write", "write_and_say"],
        scaffolding_intensity="moderate",
        content_scope="This lesson teaches the letter B within CVC word context. Students identify /b/ at the beginning and ending of words like 'bat' and 'cab'. Application requires spelling complete CVC words containing the /b/ sound.",
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
        spelling_pattern="single_sound",
        include_directionality=True,
        include_articulation=True,
        guided_practice_techniques=["magic_finger_write", "trace_and_say", "write_and_say"],
        scaffolding_intensity="heavy",
        content_scope="This lesson introduces the /m/ sound in isolation. Students will identify the /m/ sound at the beginning of words and practice writing the lowercase letter m.",
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

    @pytest.fixture(scope="class")
    def prompt(self, sample_plan):
        """Build the prompt once for all filtering tests."""
        return get_handwriting_generator_prompt(
            grade="K", letter="B", student_level="on-level",
            previously_learned=["m", "a", "s", "t"],
            skill_focus="isolating_sounds",
            activity_plan=sample_plan,
        )

    def test_contains_only_target_letter_cues(self, prompt):
        """Only letter B cues should appear, not other letters."""

        # Target letter present
        assert "B \u2013 Big line down, rainbow bump, rainbow bump" in prompt
        assert "b \u2013 Big line down, rainbow bump from the middle" in prompt

        # Other letters absent
        assert "A \u2013 Big line up" not in prompt
        assert "Z \u2013 Little line across" not in prompt
        assert "C \u2013 Start at the top" not in prompt

    def test_contains_only_target_sound_gesture(self, prompt):
        """Only /b/ gesture should appear, not other sounds."""
        assert "/b/" in prompt
        assert "Bounce a ball" in prompt

        # Other gestures absent
        assert "/z/" not in prompt
        assert "buzzing bee" not in prompt

    def test_contains_selected_activity_descriptions(self, prompt):
        """Full descriptions for selected activities should be present."""
        # Sound Spark (review activity)
        assert "chorally pronounce the sound" in prompt
        # Sound Hunt (sound target activity)
        assert "beginning, middle, or ending sound" in prompt
        # Trace & Say (handwriting activity)
        assert "dotted-line handwriting templates" in prompt
        # Sound-Letter Hunt (spelling activity)
        assert "write the corresponding letter" in prompt

    def test_excludes_non_selected_activities(self, prompt):
        """Activities NOT in the plan should not have descriptions in prompt."""
        # Finger Run — not selected
        assert "run their finger from left to right across the handwriting lines" not in prompt
        # Spell Sprint — not selected
        assert "countdown to the next word" not in prompt
        # Chop the Sound — not selected
        assert 'remove (or "chop")' not in prompt

    def test_excludes_form_d(self, prompt):
        """Form D content should not be in the prompt.

        Note: "FORM D" may appear as a cross-reference in training-codes.md
        or form-b, but the actual Form D content (activity levels) must not
        be present.
        """
        assert "form-d-scaffolded-activities" not in prompt
        assert "(low-level)" not in prompt
        assert "(middle-level)" not in prompt
        assert "(high-level)" not in prompt

    def test_excludes_form_h_on_initial_generation(self, prompt):
        """Form H modifications content should not be present.

        Note: "FORM H" may appear as a cross-reference in other forms,
        but the actual modification examples must not be loaded.
        """
        assert "Modification of Activity Examples" not in prompt

    def test_contains_universal_forms(self, prompt):
        """Forms A, B, and E should always be present."""
        # Form A — objectives verb list
        assert "Orient, Point, Match, Name" in prompt
        # Form B — lesson structure
        assert "Review & Connect" in prompt
        assert "Model, Explain & Engage" in prompt
        # Form E — best practices
        assert "evidence-based" in prompt.lower() or "proper way to hold a pencil" in prompt

    def test_contains_grade_specific_form_c(self, prompt):
        """Form C for the target grade should be present."""
        assert "FORM C" in prompt or "form-c" in prompt.lower() or "Example" in prompt

    def test_contains_previously_learned_sounds(self, prompt):
        """Previously learned sounds must appear as explicit list."""
        assert "m" in prompt
        assert "a" in prompt
        assert "s" in prompt
        assert "t" in prompt

    def test_contains_pre_selected_standards(self, prompt, sample_plan):
        """Standards from the plan should be in the prompt."""
        for code in sample_plan["standards"]:
            assert code in prompt

    def test_handwriting_chain_included_when_present(self, sample_plan_with_chain):
        """If handwriting_chain is set, its description should be in prompt."""
        prompt = get_handwriting_generator_prompt(
            grade="PreK", letter="M", student_level="struggling",
            previously_learned=[],
            skill_focus="isolating_sounds",
            activity_plan=sample_plan_with_chain,
        )

        # SkyWrite (primary handwriting)
        assert "write letters in the air" in prompt
        # Trace & Say (chain activity)
        assert "dotted-line handwriting templates" in prompt


class TestPromptParameters:
    """Test that prompt parameters are correctly substituted."""

    @pytest.fixture(scope="class")
    def prompt(self, sample_plan):
        return get_handwriting_generator_prompt(
            grade="K", letter="B", student_level="on-level",
            previously_learned=["m", "a", "s", "t"],
            skill_focus="isolating_sounds",
            activity_plan=sample_plan,
        )

    def test_grade_appears_in_prompt(self, prompt):
        assert "K" in prompt or "Kindergarten" in prompt

    def test_letter_appears_in_prompt(self, prompt):
        assert "B" in prompt

    def test_student_level_appears_in_prompt(self, prompt):
        assert "on-level" in prompt

    def test_skill_focus_appears_in_prompt(self, prompt):
        assert "isolating_sounds" in prompt or "isolating sounds" in prompt

    def test_previously_learned_in_task_header(self, prompt):
        """Previously learned sounds must appear in the Your Task section."""
        # The task header should list these as a parameter, not just in Rule 12
        assert "m, a, s, t" in prompt or "m,a,s,t" in prompt

    def test_skill_focus_in_task_header(self, prompt):
        """Skill focus must appear in the Your Task section."""
        assert "isolating_sounds" in prompt or "isolating sounds" in prompt


class TestStandardsNotInGenerator:
    """Test that the full standards reference is removed from the generator prompt."""

    @pytest.fixture(scope="class")
    def prompt(self, sample_plan):
        return get_handwriting_generator_prompt(
            grade="K", letter="B", student_level="on-level",
            previously_learned=["m", "a", "s", "t"],
            skill_focus="isolating_sounds",
            activity_plan=sample_plan,
        )

    def test_no_grade_standards_section(self, prompt):
        """The full 'Grade-Specific Standards Reference' section must be removed."""
        assert "Grade-Specific Standards Reference" not in prompt

    def test_no_full_standards_dump(self, prompt):
        """Codes not in the plan must NOT appear — proves we're not dumping all."""
        # K.F.PA.6.d is a real K code but not in our sample_plan
        assert "K.F.PA.6.d" not in prompt
        # K.F.H.2.b is a real K code but not in the plan
        assert "K.F.H.2.b" not in prompt

    def test_plan_standards_included(self, prompt, sample_plan):
        """Standards from the activity plan must appear in the prompt."""
        for code in sample_plan["standards"]:
            assert code in prompt

    def test_plan_standards_include_descriptions(self, prompt):
        """Standards must include descriptions, not just bare codes."""
        # K.F.PA.6.a description from the reference file
        assert "Isolate and pronounce initial" in prompt
        # K.F.H.1.a description
        assert "Form all uppercase and lowercase letters" in prompt

    def test_no_select_standards_instruction(self, prompt):
        """Generator must NOT be told to 'Select' standards."""
        # Old Rule 5 said "Select 1-3 standards" / "Include at least 4 standards"
        # New Rule 5 should say "Use the pre-selected standards"
        lower = prompt.lower()
        # Check that the standards sub-section doesn't instruct selection
        assert "select 1\u20133 standards" not in lower
        assert "select 1-3 standards" not in lower
        assert "include at least 4 standards, one from each" not in lower


class TestDirectivesInPrompt:
    """Test that lesson directives appear in the generator prompt and old rules do not."""

    @pytest.fixture(scope="class")
    def prompt(self, sample_plan):
        return get_handwriting_generator_prompt(
            grade="K", letter="B", student_level="on-level",
            previously_learned=["m", "a", "s", "t"],
            skill_focus="isolating_sounds",
            activity_plan=sample_plan,
        )

    def test_directives_section_present(self, prompt):
        """The 'Lesson Directives' section must appear."""
        assert "LESSON DIRECTIVES FROM ACTIVITY PLAN" in prompt

    def test_spelling_pattern_in_prompt(self, prompt):
        """Spelling pattern directive must appear."""
        assert "`CVC`" in prompt

    def test_directionality_in_prompt(self, prompt):
        """Directionality directive must appear."""
        assert "Directionality" in prompt
        assert "NO" in prompt  # K on-level → no directionality

    def test_articulation_in_prompt(self, prompt):
        """Articulation directive must appear."""
        assert "Articulation" in prompt
        assert "YES" in prompt  # K → include articulation

    def test_guided_practice_techniques_in_prompt(self, prompt):
        """Guided practice techniques must appear in order."""
        assert "trace_and_say" in prompt
        assert "say_and_write" in prompt
        assert "write_and_say" in prompt

    def test_scaffolding_intensity_in_prompt(self, prompt):
        """Scaffolding intensity must appear."""
        assert "MODERATE" in prompt

    def test_content_scope_in_prompt(self, prompt):
        """Content scope narrative must appear."""
        assert "CVC word context" in prompt

    def test_no_rule_13_letter_case(self, prompt):
        """Old Rule 13 (Letter Case) must not appear."""
        assert "Teach LOWERCASE only by default" not in prompt
        assert "no explicit formation teaching" not in prompt

    def test_no_rule_14_directionality(self, prompt):
        """Old Rule 14 details must not appear."""
        assert "ALWAYS explicitly teach — left-to-right movement, name the top" not in prompt

    def test_no_rule_15_articulation(self, prompt):
        """Old Rule 15 details must not appear."""
        assert "ALWAYS include explicit mouth/lip/tongue/vocal box instruction" not in prompt

    def test_no_rule_16_guided_practice(self, prompt):
        """Old Rule 16 details must not appear."""
        assert "Use finger tracing (Magic Finger Write) BEFORE pencil" not in prompt

    def test_no_rule_17_content_scope(self, prompt):
        """Old Rule 17 details must not appear."""
        assert "Spelling patterns (CVCe, digraphs, etc.)" not in prompt

    def test_no_rule_18_scaffolding(self, prompt):
        """Old Rule 18 details must not appear."""
        assert "Teach from scratch. Heavy scaffolding" not in prompt

    def test_no_grade_level_delivery_rules_header(self, prompt):
        """The 'GRADE-LEVEL DELIVERY RULES' header must be gone."""
        assert "GRADE-LEVEL DELIVERY RULES" not in prompt

    def test_rule_10_articulation_skip_clause(self, prompt):
        """Rule 10 must include skip clause for articulation."""
        assert "Skip this rule if `include_articulation` is false" in prompt

    def test_letter_not_forced_uppercase(self):
        """Letter should be passed through as-is, not forced to uppercase."""
        plan = ActivityPlan(
            review="sound_spark",
            sound_target="sound_hunt",
            handwriting="trace_and_say",
            handwriting_chain=None,
            spelling="sound_letter_hunt",
            standards=["K.F.PA.6.a", "K.F.P.1.a", "K.F.P.3.a", "K.F.H.1.a"],
            spelling_pattern="CVC",
            include_directionality=False,
            include_articulation=True,
            guided_practice_techniques=["trace_and_say", "say_and_write", "write_and_say"],
            scaffolding_intensity="moderate",
            content_scope="Lesson about letter b.",
        )
        prompt = get_handwriting_generator_prompt(
            grade="K", letter="b", student_level="on-level",
            previously_learned=["m", "a"],
            skill_focus="isolating_sounds",
            activity_plan=plan,
        )
        # The task header should show lowercase b
        assert "**Target Letter**: b" in prompt
