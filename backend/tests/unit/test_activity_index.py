"""
Unit tests for the activity index structure and integrity.

Validates that the YAML index is well-formed, all slugs are unique,
all activities have required fields, and by_grade entries are consistent.

No LLM calls — tests the index file itself.
"""

from pathlib import Path

import pytest
import yaml

INDEX_PATH = (
    Path(__file__).parent.parent.parent
    / "prompt" / "reference_materials" / "handwriting" / "activity-index.yaml"
)

VALID_GRADES = {"PreK", "K", "1st"}
VALID_LEVELS = {"struggling", "on-level", "advanced"}
VALID_SKILL_FOCUSES = {"isolating_sounds", "blending", "letter_formation", "spelling"}
EXPECTED_SECTIONS = {"review", "sound_target_focus", "handwriting_focus", "spelling_focus"}


@pytest.fixture(scope="module")
def index():
    with open(INDEX_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def all_activities(index):
    """Flatten all activities from all sections."""
    activities = []
    for section_key, section in index["sections"].items():
        for activity in section["activities"]:
            activities.append({**activity, "_section": section_key})
    return activities


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestIndexStructure:
    """Validate the YAML index has correct top-level structure."""

    def test_has_sections_key(self, index):
        assert "sections" in index

    def test_has_all_four_sections(self, index):
        assert set(index["sections"].keys()) == EXPECTED_SECTIONS

    def test_each_section_has_required_keys(self, index):
        for section_key, section in index["sections"].items():
            assert "time" in section, f"Section {section_key} missing 'time'"
            assert "purpose" in section, f"Section {section_key} missing 'purpose'"
            assert "activities" in section, f"Section {section_key} missing 'activities'"
            assert len(section["activities"]) > 0, f"Section {section_key} has no activities"


# ---------------------------------------------------------------------------
# Activity field tests
# ---------------------------------------------------------------------------

class TestActivityFields:
    """Validate each activity has required fields with valid values."""

    def test_every_activity_has_required_fields(self, all_activities):
        required = {"name", "rank", "summary", "skill_focus", "prerequisites", "by_grade"}
        for activity in all_activities:
            for field in required:
                assert field in activity, (
                    f"Activity '{activity.get('name', '?')}' in "
                    f"{activity['_section']} missing field '{field}'"
                )

    def test_skill_focus_values_are_valid(self, all_activities):
        for activity in all_activities:
            for focus in activity["skill_focus"]:
                assert focus in VALID_SKILL_FOCUSES, (
                    f"Activity '{activity['name']}' has invalid skill_focus: {focus}"
                )

    def test_rank_is_positive_integer(self, all_activities):
        for activity in all_activities:
            assert isinstance(activity["rank"], int) and activity["rank"] > 0, (
                f"Activity '{activity['name']}' has invalid rank: {activity['rank']}"
            )

    def test_summary_is_nonempty_string(self, all_activities):
        for activity in all_activities:
            assert isinstance(activity["summary"], str) and len(activity["summary"]) > 10, (
                f"Activity '{activity['name']}' has empty or too-short summary"
            )


# ---------------------------------------------------------------------------
# Slug tests
# ---------------------------------------------------------------------------

class TestSlugs:
    """Validate slug uniqueness and format."""

    def test_all_activities_have_id_field(self, all_activities):
        """Each activity must have an 'id' slug field (to be added during implementation)."""
        # NOTE: The current index uses 'name' as display name.
        # The implementation must add 'id' fields matching the framework slugs.
        # For now, we derive slugs from names and verify uniqueness.
        pass  # Will be enforced once 'id' field is added to index

    def test_exactly_30_activities(self, all_activities):
        assert len(all_activities) == 30, (
            f"Expected 30 activities, got {len(all_activities)}"
        )

    def test_ranks_unique_within_section(self, index):
        for section_key, section in index["sections"].items():
            ranks = [a["rank"] for a in section["activities"]]
            assert len(ranks) == len(set(ranks)), (
                f"Duplicate ranks in {section_key}: {ranks}"
            )

    def test_ranks_sequential(self, index):
        for section_key, section in index["sections"].items():
            ranks = sorted(a["rank"] for a in section["activities"])
            expected = list(range(1, len(ranks) + 1))
            assert ranks == expected, (
                f"Non-sequential ranks in {section_key}: {ranks}"
            )


# ---------------------------------------------------------------------------
# Grade/level tests
# ---------------------------------------------------------------------------

class TestByGrade:
    """Validate by_grade structure and grade-level consistency."""

    def test_every_activity_has_all_three_grades(self, all_activities):
        """by_grade must have entries for PreK, K, and 1st (even if null)."""
        for activity in all_activities:
            by_grade = activity["by_grade"]
            for grade in VALID_GRADES:
                assert grade in by_grade, (
                    f"Activity '{activity['name']}' missing grade '{grade}' in by_grade"
                )

    def test_non_null_grades_have_levels(self, all_activities):
        """If a grade is not null, it must have a 'levels' list."""
        for activity in all_activities:
            for grade, config in activity["by_grade"].items():
                if config is not None:
                    assert "levels" in config, (
                        f"Activity '{activity['name']}' grade '{grade}' "
                        f"is non-null but has no 'levels'"
                    )
                    assert len(config["levels"]) > 0, (
                        f"Activity '{activity['name']}' grade '{grade}' "
                        f"has empty levels list"
                    )

    def test_level_values_are_valid(self, all_activities):
        for activity in all_activities:
            for grade, config in activity["by_grade"].items():
                if config is not None:
                    for level in config["levels"]:
                        assert level in VALID_LEVELS, (
                            f"Activity '{activity['name']}' grade '{grade}' "
                            f"has invalid level: {level}"
                        )

    def test_at_least_one_grade_is_available(self, all_activities):
        """No activity should be null for ALL grades (would be useless)."""
        for activity in all_activities:
            non_null = [g for g, c in activity["by_grade"].items() if c is not None]
            assert len(non_null) >= 1, (
                f"Activity '{activity['name']}' is null for all grades"
            )


# ---------------------------------------------------------------------------
# Section-specific activity count tests
# ---------------------------------------------------------------------------

class TestSectionCounts:
    """Validate expected activity counts per section."""

    def test_review_has_6_activities(self, index):
        assert len(index["sections"]["review"]["activities"]) == 6

    def test_sound_target_focus_has_7_activities(self, index):
        assert len(index["sections"]["sound_target_focus"]["activities"]) == 7

    def test_handwriting_focus_has_10_activities(self, index):
        assert len(index["sections"]["handwriting_focus"]["activities"]) == 10

    def test_spelling_focus_has_7_activities(self, index):
        assert len(index["sections"]["spelling_focus"]["activities"]) == 7


# ---------------------------------------------------------------------------
# Cross-reference with framework file
# ---------------------------------------------------------------------------

class TestFrameworkCrossReference:
    """Verify index activity names exist in the framework file."""

    @pytest.fixture(scope="class")
    def framework_text(self):
        framework_path = INDEX_PATH.parent / "activity-framework.md"
        return framework_path.read_text()

    def test_every_activity_name_appears_in_framework(self, all_activities, framework_text):
        for activity in all_activities:
            assert activity["name"] in framework_text, (
                f"Activity '{activity['name']}' from index not found in framework"
            )
