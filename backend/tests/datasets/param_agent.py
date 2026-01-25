"""
Test dataset for parameter collection agent evaluation.

This is the source of truth for param agent test cases.
Can be synced to Langfuse dataset 'param-agent-eval' for production evals.
"""

from dataclasses import dataclass
from typing import Union, List, Dict, Optional


@dataclass
class ParamTestCase:
    """
    A single test case for param agent evaluation.

    Attributes:
        input: User message(s) - either a single string or list of message dicts
        task_type: The task type from routing (always "handwriting" for now)
        expected_params: Expected extracted parameters (or None if params shouldn't be extracted)
        description: Human-readable description of the test case
        category: Test category for grouping
    """
    input: Union[str, List[Dict[str, str]]]
    task_type: str
    expected_params: Optional[Dict[str, str]]
    description: str
    category: str


# --- Test Cases ---

PARAM_TEST_CASES: List[ParamTestCase] = [
    # ==========================================
    # Category: All params in one message (4)
    # ==========================================
    ParamTestCase(
        input="PreK letter A",
        task_type="handwriting",
        expected_params={"grade": "PreK", "letter": "A", "student_level": "on-level"},
        description="All params: PreK letter A",
        category="complete",
    ),
    ParamTestCase(
        input="I need a handwriting lesson for letter B, kindergarten level",
        task_type="handwriting",
        expected_params={"grade": "K", "letter": "B", "student_level": "on-level"},
        description="All params: K letter B with context",
        category="complete",
    ),
    ParamTestCase(
        input="1st grade, letter C",
        task_type="handwriting",
        expected_params={"grade": "1st", "letter": "C", "student_level": "on-level"},
        description="All params: 1st grade letter C",
        category="complete",
    ),
    ParamTestCase(
        input="letter D for pre-k students",
        task_type="handwriting",
        expected_params={"grade": "PreK", "letter": "D", "student_level": "on-level"},
        description="All params: PreK (variation) letter D",
        category="complete",
    ),

    # ==========================================
    # Category: Missing grade (3)
    # ==========================================
    ParamTestCase(
        input="letter E",
        task_type="handwriting",
        expected_params=None,  # Should ask for grade
        description="Missing grade: only letter E",
        category="missing_grade",
    ),
    ParamTestCase(
        input="I want to practice letter F",
        task_type="handwriting",
        expected_params=None,  # Should ask for grade
        description="Missing grade: letter F with context",
        category="missing_grade",
    ),
    ParamTestCase(
        input="help with the letter G please",
        task_type="handwriting",
        expected_params=None,  # Should ask for grade
        description="Missing grade: polite request letter G",
        category="missing_grade",
    ),

    # ==========================================
    # Category: Missing letter (3)
    # ==========================================
    ParamTestCase(
        input="PreK handwriting lesson",
        task_type="handwriting",
        expected_params=None,  # Should ask for letter
        description="Missing letter: only grade PreK",
        category="missing_letter",
    ),
    ParamTestCase(
        input="kindergarten",
        task_type="handwriting",
        expected_params=None,  # Should ask for letter
        description="Missing letter: only grade K",
        category="missing_letter",
    ),
    ParamTestCase(
        input="first grade handwriting practice",
        task_type="handwriting",
        expected_params=None,  # Should ask for letter
        description="Missing letter: 1st grade with context",
        category="missing_letter",
    ),

    # ==========================================
    # Category: With student level specified (3)
    # ==========================================
    ParamTestCase(
        input="PreK letter H for struggling students",
        task_type="handwriting",
        expected_params={"grade": "PreK", "letter": "H", "student_level": "struggling"},
        description="With level: struggling students",
        category="with_level",
    ),
    ParamTestCase(
        input="kindergarten letter I, advanced level",
        task_type="handwriting",
        expected_params={"grade": "K", "letter": "I", "student_level": "advanced"},
        description="With level: advanced level",
        category="with_level",
    ),
    ParamTestCase(
        input="1st grade letter J for on-level students",
        task_type="handwriting",
        expected_params={"grade": "1st", "letter": "J", "student_level": "on-level"},
        description="With level: explicit on-level",
        category="with_level",
    ),

    # ==========================================
    # Category: Invalid inputs (3)
    # ==========================================
    ParamTestCase(
        input="5th grade letter K",
        task_type="handwriting",
        expected_params=None,  # Should explain valid grades
        description="Invalid: 5th grade not valid",
        category="invalid",
    ),
    ParamTestCase(
        input="2nd grade letter L",
        task_type="handwriting",
        expected_params=None,  # Should explain valid grades
        description="Invalid: 2nd grade not valid",
        category="invalid",
    ),
    ParamTestCase(
        input="middle school letter M",
        task_type="handwriting",
        expected_params=None,  # Should explain valid grades
        description="Invalid: middle school not valid",
        category="invalid",
    ),

    # ==========================================
    # Category: Edge cases (2)
    # ==========================================
    ParamTestCase(
        input="prek Letter a",
        task_type="handwriting",
        expected_params={"grade": "PreK", "letter": "A", "student_level": "on-level"},
        description="Edge: case insensitive letter",
        category="edge",
    ),
    ParamTestCase(
        input="K, z",
        task_type="handwriting",
        expected_params={"grade": "K", "letter": "Z", "student_level": "on-level"},
        description="Edge: minimal input K z",
        category="edge",
    ),
]


def get_test_cases_by_category(category: str) -> List[ParamTestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in PARAM_TEST_CASES if tc.category == category]


def get_all_test_cases() -> List[ParamTestCase]:
    """Get all test cases."""
    return PARAM_TEST_CASES


def get_extraction_cases() -> List[ParamTestCase]:
    """Get all test cases where param extraction is expected."""
    return [tc for tc in PARAM_TEST_CASES if tc.expected_params is not None]


def get_clarification_cases() -> List[ParamTestCase]:
    """Get all test cases where clarification is expected (no extraction)."""
    return [tc for tc in PARAM_TEST_CASES if tc.expected_params is None]
