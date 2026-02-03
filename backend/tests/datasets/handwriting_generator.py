"""
Test dataset for handwriting generator agent evaluation.

This is the source of truth for handwriting generator test cases.
Can be synced to Langfuse dataset 'handwriting-generator-eval' for production evals.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HandwritingGeneratorTestCase:
    """
    A single test case for handwriting generator evaluation.

    Attributes:
        handwriting_params: Input params (grade, letter, student_level)
        expected_sections: List of required sections that must be present
        expected_verbal_cues: Expected verbal cues for target letter
        description: Human-readable description of the test case
        category: Test category for grouping
    """
    handwriting_params: dict
    expected_sections: List[str]
    expected_verbal_cues: Optional[str]
    description: str
    category: str


# Standard required sections for all lessons
REQUIRED_SECTIONS = [
    "standards",
    "objectives",
    "materials",
    "review & connect",
    "model, explain & engage",
    "guided practice",
    "application",
    "wrap-up",
]


# --- Test Cases ---

HANDWRITING_GENERATOR_TEST_CASES: List[HandwritingGeneratorTestCase] = [
    # ==========================================
    # Category: basic_generation (5)
    # Different letters and grades
    # ==========================================
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "A",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line up, big line down, little line across",
        description="Basic: PreK letter A on-level",
        category="basic_generation",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "K",
            "letter": "B",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, rainbow bump, rainbow bump",
        description="Basic: K letter B on-level",
        category="basic_generation",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "1st",
            "letter": "Z",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Little line across, slant down, little line across",
        description="Basic: 1st letter Z on-level",
        category="basic_generation",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "M",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, rainbow bump, rainbow bump",
        description="Basic: PreK letter M on-level",
        category="basic_generation",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "Z",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Little line across, slant down, little line across",
        description="Basic: PreK letter Z on-level",
        category="basic_generation",
    ),

    # ==========================================
    # Category: struggling_level (2)
    # Should use low-level activities from Form D
    # ==========================================
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "S",
            "student_level": "struggling",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Little curve this way, little curve that way",
        description="Struggling: PreK letter S",
        category="struggling_level",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "K",
            "letter": "C",
            "student_level": "struggling",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Start at the top, curve around like a rainbow",
        description="Struggling: K letter C",
        category="struggling_level",
    ),

    # ==========================================
    # Category: advanced_level (2)
    # Should use high-level activities from Form D
    # ==========================================
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "1st",
            "letter": "Q",
            "student_level": "advanced",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big curve around, close it up, little line out",
        description="Advanced: 1st letter Q",
        category="advanced_level",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "K",
            "letter": "W",
            "student_level": "advanced",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Slant down, slant up, slant down, slant up",
        description="Advanced: K letter W",
        category="advanced_level",
    ),

    # ==========================================
    # Category: verbal_cues (4)
    # Verify correct cues for various letters
    # ==========================================
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "E",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, little line at the top, middle, and bottom",
        description="Verbal cues: letter E",
        category="verbal_cues",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "K",
            "letter": "R",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, rainbow bump, slant out",
        description="Verbal cues: letter R",
        category="verbal_cues",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "1st",
            "letter": "X",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Slant down, slant the other way",
        description="Verbal cues: letter X",
        category="verbal_cues",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "PreK",
            "letter": "O",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big curve around, close it up",
        description="Verbal cues: letter O",
        category="verbal_cues",
    ),

    # ==========================================
    # Category: structure (2)
    # Verify all sections present and properly formatted
    # ==========================================
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "K",
            "letter": "T",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, little line across the top",
        description="Structure: all sections present for letter T",
        category="structure",
    ),
    HandwritingGeneratorTestCase(
        handwriting_params={
            "grade": "1st",
            "letter": "P",
            "student_level": "on-level",
        },
        expected_sections=REQUIRED_SECTIONS,
        expected_verbal_cues="Big line down, rainbow bump",
        description="Structure: all sections present for letter P",
        category="structure",
    ),
]


def get_test_cases_by_category(category: str) -> List[HandwritingGeneratorTestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in HANDWRITING_GENERATOR_TEST_CASES if tc.category == category]


def get_all_test_cases() -> List[HandwritingGeneratorTestCase]:
    """Get all test cases."""
    return HANDWRITING_GENERATOR_TEST_CASES


def get_basic_generation_cases() -> List[HandwritingGeneratorTestCase]:
    """Get basic generation test cases."""
    return get_test_cases_by_category("basic_generation")


def get_struggling_level_cases() -> List[HandwritingGeneratorTestCase]:
    """Get struggling level test cases."""
    return get_test_cases_by_category("struggling_level")


def get_advanced_level_cases() -> List[HandwritingGeneratorTestCase]:
    """Get advanced level test cases."""
    return get_test_cases_by_category("advanced_level")


def get_verbal_cues_cases() -> List[HandwritingGeneratorTestCase]:
    """Get verbal cues test cases."""
    return get_test_cases_by_category("verbal_cues")


def get_structure_cases() -> List[HandwritingGeneratorTestCase]:
    """Get structure test cases."""
    return get_test_cases_by_category("structure")
