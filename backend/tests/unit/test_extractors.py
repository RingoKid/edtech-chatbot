"""
Unit tests for reference material extraction functions.

Tests regex-based extraction of activity descriptions, verbal cues,
phoneme gestures, and grade-specific standards from reference files.

These tests run against the actual reference material files on disk.
No LLM calls, no network — pure Python regex validation.
"""

import re
from pathlib import Path

import pytest

# Path to reference materials
REFERENCE_DIR = Path(__file__).parent.parent.parent / "prompt" / "reference_materials"
HANDWRITING_DIR = REFERENCE_DIR / "handwriting"
FORM_F_PATH = HANDWRITING_DIR / "form-f-verbal-cues.md"
FORM_G_PATH = HANDWRITING_DIR / "form-g-phoneme-gestures.md"
FRAMEWORK_PATH = HANDWRITING_DIR / "activity-framework.md"
STANDARDS_PATH = REFERENCE_DIR / "handwriting-spelling-standards.md"

from app.graph.utils.extractors import (
    extract_activity,
    extract_verbal_cues,
    extract_gesture,
    extract_grade_standards,
    extract_standard,
    LETTER_TO_SOUNDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def framework_text():
    return FRAMEWORK_PATH.read_text()


@pytest.fixture(scope="module")
def form_f_text():
    return FORM_F_PATH.read_text()


@pytest.fixture(scope="module")
def form_g_text():
    return FORM_G_PATH.read_text()


@pytest.fixture(scope="module")
def standards_text():
    return STANDARDS_PATH.read_text()


# ---------------------------------------------------------------------------
# Activity extraction tests
# ---------------------------------------------------------------------------

class TestExtractActivity:
    """Test activity description extraction from the activity framework."""

    def test_extracts_first_activity(self, framework_text):
        result = extract_activity(framework_text, "sound_echo")
        assert "The teacher says the sound first" in result
        assert "phonological loop" in result

    def test_extracts_middle_activity(self, framework_text):
        result = extract_activity(framework_text, "sound_spark")
        assert "chorally pronounce the sound" in result
        assert "90% successful with Tap the Sound" in result

    def test_extracts_last_activity_in_section(self, framework_text):
        result = extract_activity(framework_text, "how_many_sounds")
        assert "manipulative to count" in result
        # Should not bleed into next section
        assert "Sound Target Focus" not in result

    def test_extracts_last_activity_in_file(self, framework_text):
        result = extract_activity(framework_text, "spell_sprint")
        assert "dictates words" in result
        assert "spelling fluency" in result

    def test_disambiguates_write_the_sound_review(self, framework_text):
        result = extract_activity(framework_text, "write_the_sound_review")
        assert "mini whiteboard" in result
        assert "review activity" in result
        # Should NOT contain spelling section content
        assert "handwriting sheet" not in result or "retrieve the grapheme" in result

    def test_disambiguates_write_the_sound_spelling(self, framework_text):
        result = extract_activity(framework_text, "write_the_sound_spelling")
        assert "handwriting sheet" in result
        assert "no tracing provided" in result

    def test_returns_empty_for_nonexistent_slug(self, framework_text):
        assert extract_activity(framework_text, "nonexistent_activity") == ""

    def test_multiline_content_preserved(self, framework_text):
        result = extract_activity(framework_text, "sound_hunt")
        # Sound Hunt has multiple paragraphs and numbered examples
        assert "beginning, middle, or ending" in result
        assert "two ways teachers can use" in result
        assert "Example (listening for the beginning sound)" in result

    def test_all_30_slugs_extractable(self, framework_text):
        """Every slug in the index must produce non-empty extraction."""
        all_slugs = [
            # Review
            "sound_echo", "tap_that_sound", "sound_spark",
            "write_the_sound_review", "sort_the_sound", "how_many_sounds",
            # Sound Target Focus
            "sound_check", "word_sound_echo", "sound_hunt",
            "silly_sentence", "stretch_the_sounds", "chop_the_sound",
            "sound_switch_a_roo",
            # Handwriting Focus
            "finger_run", "skywrite", "finger_trace", "magic_finger_write",
            "trace_and_say", "start_dot_and_say", "write_the_sound_challenge",
            "cover_and_try", "disappearing_letter", "letter_sprint",
            # Spelling Focus
            "trace_the_sound", "write_the_sound_spelling", "sound_letter_hunt",
            "stretch_and_write", "switch_a_roo_write", "sentence_challenge",
            "spell_sprint",
        ]
        for slug in all_slugs:
            result = extract_activity(framework_text, slug)
            assert result, f"Empty extraction for slug: {slug}"
            assert len(result) > 50, f"Suspiciously short extraction for slug: {slug}"


# ---------------------------------------------------------------------------
# Verbal cue extraction tests
# ---------------------------------------------------------------------------

class TestExtractVerbalCues:
    """Test verbal cue extraction from Form F."""

    def test_extracts_uppercase_and_lowercase(self, form_f_text):
        result = extract_verbal_cues(form_f_text, "B")
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) == 2
        assert any("Big line down, rainbow bump, rainbow bump" in l for l in lines)
        assert any("Big line down, rainbow bump from the middle" in l for l in lines)

    def test_extracts_letter_a(self, form_f_text):
        result = extract_verbal_cues(form_f_text, "A")
        assert "Big line up, big line down, little line across" in result
        assert "rainbow around" in result  # lowercase a

    def test_extracts_letter_z(self, form_f_text):
        result = extract_verbal_cues(form_f_text, "Z")
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) == 2

    def test_no_false_positive_from_cue_text(self, form_f_text):
        """Letter 'I' should not match 'in' appearing in other cues."""
        result = extract_verbal_cues(form_f_text, "I")
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) == 2  # only I and i
        assert all(l.startswith("I ") or l.startswith("i ") for l in lines)

    def test_excludes_other_letters(self, form_f_text):
        result = extract_verbal_cues(form_f_text, "B")
        assert "A " not in result.split("\n")[0]
        assert "C " not in result

    def test_returns_empty_for_nonexistent(self, form_f_text):
        assert extract_verbal_cues(form_f_text, "0") == ""

    @pytest.mark.parametrize("letter", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    def test_every_letter_has_cues(self, form_f_text, letter):
        """Every letter A-Z must return exactly 2 lines (upper + lower)."""
        result = extract_verbal_cues(form_f_text, letter)
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) == 2, f"Expected 2 cues for {letter}, got {len(lines)}"


# ---------------------------------------------------------------------------
# Gesture extraction tests
# ---------------------------------------------------------------------------

class TestExtractGesture:
    """Test phoneme gesture extraction from Form G."""

    def test_extracts_consonant(self, form_g_text):
        result = extract_gesture(form_g_text, "b")
        assert "/b/" in result
        assert "Bounce a ball" in result

    def test_extracts_vowel_short_and_long(self, form_g_text):
        """Vowels must return BOTH short and long sound rows."""
        result = extract_gesture(form_g_text, "a")
        assert "/a/" in result
        assert "/\u0101/" in result
        assert "apple" in result
        assert "cake" in result

    def test_extracts_all_vowels_both_sounds(self, form_g_text):
        for vowel in "aeiou":
            result = extract_gesture(form_g_text, vowel)
            lines = [l for l in result.strip().splitlines()
                     if l.startswith("|") and "Phoneme" not in l and "---" not in l]
            assert len(lines) >= 2, f"Vowel {vowel} should have short + long rows"

    def test_no_cross_column_match(self, form_g_text):
        """Should not match a sound appearing in gesture description text."""
        result = extract_gesture(form_g_text, "b")
        # /b/ appears only in the phoneme column, not gesture text
        data_rows = [l for l in result.strip().splitlines()
                     if l.startswith("|") and "Phoneme" not in l and "---" not in l]
        for row in data_rows:
            first_col = row.split("|")[1]
            assert "/b/" in first_col

    def test_includes_table_header(self, form_g_text):
        result = extract_gesture(form_g_text, "z")
        assert "Phoneme" in result
        assert "---" in result

    def test_q_maps_to_qu(self, form_g_text):
        result = extract_gesture(form_g_text, "q")
        assert "/qu/" in result
        assert "queen" in result

    def test_returns_header_only_for_nonexistent(self, form_g_text):
        """Unknown letter returns at most headers, no data rows."""
        result = extract_gesture(form_g_text, "0")
        data_rows = [l for l in result.strip().splitlines()
                     if l.startswith("|") and "Phoneme" not in l and "---" not in l]
        assert len(data_rows) == 0

    @pytest.mark.parametrize("letter", list("bcdfghjklmnprstvwyz"))
    def test_every_consonant_has_gesture(self, form_g_text, letter):
        """Every consonant must return at least 1 data row."""
        result = extract_gesture(form_g_text, letter)
        data_rows = [l for l in result.strip().splitlines()
                     if l.startswith("|") and "Phoneme" not in l and "---" not in l]
        assert len(data_rows) >= 1, f"No gesture found for consonant {letter}"


# ---------------------------------------------------------------------------
# Standards extraction tests
# ---------------------------------------------------------------------------

class TestExtractGradeStandards:
    """Test grade-specific standards extraction."""

    def test_extracts_prek_section(self, standards_text):
        result = extract_grade_standards(standards_text, "PreK")
        assert "GELDS" in result
        assert "CLL6" in result
        assert "CLL9" in result
        # Should NOT contain K or 1st grade content
        assert "K.F.PA" not in result
        assert "1.F.PA" not in result

    def test_extracts_kindergarten_section(self, standards_text):
        result = extract_grade_standards(standards_text, "Kindergarten")
        assert "K.F.PA" in result
        assert "K.F.P" in result
        assert "K.F.H" in result
        # Should NOT contain PreK or 1st grade content
        assert "GELDS" not in result
        assert "1.F.PA" not in result

    def test_extracts_first_grade_section(self, standards_text):
        result = extract_grade_standards(standards_text, "1st Grade")
        assert "1.F.PA" in result
        assert "1.F.P" in result
        assert "1.F.H" in result
        # Should NOT contain PreK or K content (note: "K.F.PA" may appear
        # in explanatory text, so we check for actual K standard entries)
        assert "GELDS" not in result
        assert "| K.F.PA" not in result  # actual K standard table entries

    def test_returns_empty_for_nonexistent_grade(self, standards_text):
        assert extract_grade_standards(standards_text, "2nd Grade") == ""

    def test_prek_has_cll_codes(self, standards_text):
        result = extract_grade_standards(standards_text, "PreK")
        cll_codes = re.findall(r"CLL\d+\.\d+[a-z]", result)
        assert len(cll_codes) >= 4  # at least 4 CLL codes

    def test_k_has_four_domains(self, standards_text):
        result = extract_grade_standards(standards_text, "Kindergarten")
        assert "K.F.PA" in result   # Phonemic Awareness
        assert "K.F.P.1" in result  # Phonics
        assert "K.F.P.3" in result  # Encoding
        assert "K.F.H" in result    # Handwriting


# ---------------------------------------------------------------------------
# Individual standard extraction tests
# ---------------------------------------------------------------------------

class TestExtractStandard:
    """Test single standard code + description extraction."""

    def test_extracts_k_pa_code(self, standards_text):
        result = extract_standard(standards_text, "K.F.PA.6.a")
        assert "K.F.PA.6.a" in result
        assert "Isolate and pronounce initial" in result

    def test_extracts_k_phonics_code(self, standards_text):
        result = extract_standard(standards_text, "K.F.P.1.a")
        assert "K.F.P.1.a" in result
        assert "phoneme-grapheme correspondences" in result

    def test_extracts_k_encoding_code(self, standards_text):
        result = extract_standard(standards_text, "K.F.P.3.a")
        assert "K.F.P.3.a" in result
        assert "encode simple one-syllable words" in result

    def test_extracts_k_handwriting_code(self, standards_text):
        result = extract_standard(standards_text, "K.F.H.1.a")
        assert "K.F.H.1.a" in result
        assert "Form all uppercase and lowercase letters" in result

    def test_extracts_prek_cll_code(self, standards_text):
        result = extract_standard(standards_text, "CLL6.4c")
        assert "CLL6.4c" in result
        assert "Isolates the initial" in result

    def test_extracts_1st_grade_code(self, standards_text):
        result = extract_standard(standards_text, "1.F.PA.6.a")
        assert "1.F.PA.6.a" in result
        assert "Isolate and pronounce initial, medial, and final" in result

    def test_returns_empty_for_fabricated_code(self, standards_text):
        """Fabricated codes that look plausible must return empty."""
        assert extract_standard(standards_text, "K.F.ASR.1") == ""
        assert extract_standard(standards_text, "K.F.PGR.3") == ""
        assert extract_standard(standards_text, "K.F.ENC.1") == ""
        assert extract_standard(standards_text, "K.F.HWR.1") == ""

    def test_no_partial_match(self, standards_text):
        """'K.F.PA.6' should NOT match 'K.F.PA.6.a'."""
        assert extract_standard(standards_text, "K.F.PA.6") == ""

    def test_no_cross_grade_bleed(self, standards_text):
        """K and 1st codes are distinct — extracting one must not return the other."""
        k_result = extract_standard(standards_text, "K.F.H.1.a")
        first_result = extract_standard(standards_text, "1.F.H.1.a")
        assert "K.F.H.1.a" in k_result
        assert "1.F.H.1.a" not in k_result
        assert "1.F.H.1.a" in first_result
        assert "K.F.H.1.a" not in first_result

    def test_all_prek_codes_extractable(self, standards_text):
        """Every PreK CLL code in the reference must return non-empty."""
        prek_codes = [
            "CLL6.4c", "CLL6.4e", "CLL6.4f",
            "CLL7.4a", "CLL8.4b", "CLL9.4d",
        ]
        for code in prek_codes:
            result = extract_standard(standards_text, code)
            assert result, f"Empty extraction for PreK code: {code}"

    def test_all_k_codes_extractable(self, standards_text):
        """Every K code in the reference must return non-empty."""
        k_codes = [
            "K.F.PA.6.a", "K.F.PA.6.b", "K.F.PA.6.c", "K.F.PA.6.d",
            "K.F.P.1.a", "K.F.P.1.b",
            "K.F.P.3.a", "K.F.P.3.b",
            "K.F.H.1.a", "K.F.H.1.b", "K.F.H.1.c",
            "K.F.H.2.a", "K.F.H.2.b",
        ]
        for code in k_codes:
            result = extract_standard(standards_text, code)
            assert result, f"Empty extraction for K code: {code}"

    def test_all_1st_codes_extractable(self, standards_text):
        """Every 1st grade code in the reference must return non-empty."""
        first_codes = [
            "1.F.PA.4.d",
            "1.F.PA.5.a", "1.F.PA.5.b",
            "1.F.PA.6.a", "1.F.PA.6.b", "1.F.PA.6.c", "1.F.PA.6.d",
            "1.F.P.1.a", "1.F.P.1.b",
            "1.F.P.3.a", "1.F.P.3.b", "1.F.P.3.c", "1.F.P.3.d",
            "1.F.H.1.a", "1.F.H.1.b", "1.F.H.1.c",
            "1.F.H.2.a", "1.F.H.2.b",
        ]
        for code in first_codes:
            result = extract_standard(standards_text, code)
            assert result, f"Empty extraction for 1st code: {code}"
