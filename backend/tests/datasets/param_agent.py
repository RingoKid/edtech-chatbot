"""
Test dataset for handwriting parameter collection agent evaluation.

Multi-turn support: each test case has a list of messages simulating
a conversation where the teacher provides info across multiple turns.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParamTestCase:
    """
    A single test case for the param agent evaluation.

    Attributes:
        messages: Ordered user messages (multi-turn conversation)
        expected_params: Expected extracted parameters, or None if submission should NOT happen
        expect_submit_after: Turn index (0-based) that triggers submission, or None if never
        description: Human-readable description
        category: Test category for grouping
    """
    messages: list[str]
    expected_params: dict | None
    expect_submit_after: int | None
    description: str
    category: str


# --- Test Cases ---

PARAM_TEST_CASES: list[ParamTestCase] = [
    # ==========================================
    # Category: complete — all info in one message
    # ==========================================
    ParamTestCase(
        messages=["PreK letter m, they've learned a s t, focus on blending, struggling"],
        expected_params={
            "grade": "PreK",
            "letter": "m",
            "student_level": "struggling",
            "previously_learned": ["a", "s", "t"],
            "skill_focus": "blending",
        },
        expect_submit_after=0,
        description="Complete: all 5 explicit",
        category="complete",
    ),
    ParamTestCase(
        messages=["K letter b on-level, first lesson ever, isolating sounds"],
        expected_params={
            "grade": "K",
            "letter": "b",
            "student_level": "on-level",
            "previously_learned": [],
            "skill_focus": "isolating_sounds",
        },
        expect_submit_after=0,
        description="Complete: all with defaults",
        category="complete",
    ),
    ParamTestCase(
        messages=["1st grade, letter i, they know m a s t p, work on spelling please"],
        expected_params={
            "grade": "1st",
            "letter": "i",
            "student_level": "on-level",
            "previously_learned": ["m", "a", "s", "t", "p"],
            "skill_focus": "spelling",
        },
        expect_submit_after=0,
        description="Complete: natural phrasing",
        category="complete",
    ),
    ParamTestCase(
        messages=["K letter b advanced, they know m a s t p, focus on letter formation"],
        expected_params={
            "grade": "K",
            "letter": "b",
            "student_level": "advanced",
            "previously_learned": ["m", "a", "s", "t", "p"],
            "skill_focus": "letter_formation",
        },
        expect_submit_after=0,
        description="Complete: letter_formation skill_focus",
        category="complete",
    ),

    # ==========================================
    # Category: multi_turn — info spread across turns
    # ==========================================
    ParamTestCase(
        messages=[
            "PreK letter m",
            "the students have already learned a and s",
            "I'd like to focus on blending please",
        ],
        expected_params={
            "grade": "PreK",
            "letter": "m",
            "student_level": "on-level",
            "previously_learned": ["a", "s"],
            "skill_focus": "blending",
        },
        expect_submit_after=2,
        description="Multi-turn: grade+letter then rest",
        category="multi_turn",
    ),
    ParamTestCase(
        messages=[
            "kindergarten",
            "we're working on letter b",
            "they've already learned m, a, s, and t",
            "let's focus on letter formation",
        ],
        expected_params={
            "grade": "K",
            "letter": "b",
            "student_level": "on-level",
            "previously_learned": ["m", "a", "s", "t"],
            "skill_focus": "letter_formation",
        },
        expect_submit_after=3,
        description="Multi-turn: one at a time",
        category="multi_turn",
    ),
    ParamTestCase(
        messages=[
            "K letter b struggling",
            "they've already learned m, a, s, and t",
            "focus on isolating sounds please",
        ],
        expected_params={
            "grade": "K",
            "letter": "b",
            "student_level": "struggling",
            "previously_learned": ["m", "a", "s", "t"],
            "skill_focus": "isolating_sounds",
        },
        expect_submit_after=2,
        description="Multi-turn: grade+letter+level then rest",
        category="multi_turn",
    ),

    # ==========================================
    # Category: partial_no_submit — should NOT submit
    # ==========================================
    ParamTestCase(
        messages=["PreK letter m"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: grade + letter only",
        category="partial_no_submit",
    ),
    ParamTestCase(
        messages=["K letter b struggling"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: grade + letter + level",
        category="partial_no_submit",
    ),
    ParamTestCase(
        messages=["kindergarten"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: grade only",
        category="partial_no_submit",
    ),
    ParamTestCase(
        messages=["letter b"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: letter only",
        category="partial_no_submit",
    ),
    ParamTestCase(
        messages=["K letter b on-level, they've learned m a s t"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: missing skill_focus",
        category="partial_no_submit",
    ),
    ParamTestCase(
        messages=["K letter b on-level, focus on letter formation"],
        expected_params=None,
        expect_submit_after=None,
        description="Partial: missing previously_learned",
        category="partial_no_submit",
    ),

    # ==========================================
    # Category: invalid — should ask for correction
    # ==========================================
    ParamTestCase(
        messages=["5th grade letter m"],
        expected_params=None,
        expect_submit_after=None,
        description="Invalid: 5th grade",
        category="invalid",
    ),
    ParamTestCase(
        messages=["2nd grade letter b"],
        expected_params=None,
        expect_submit_after=None,
        description="Invalid: 2nd grade",
        category="invalid",
    ),
]


def get_all_cases() -> list[ParamTestCase]:
    """Get all test cases."""
    return PARAM_TEST_CASES


def get_cases_by_category(category: str) -> list[ParamTestCase]:
    """Get test cases for a specific category."""
    return [tc for tc in PARAM_TEST_CASES if tc.category == category]


def get_complete_cases() -> list[ParamTestCase]:
    """Get cases where all info is in one message (complete extraction expected)."""
    return get_cases_by_category("complete")


def get_multi_turn_cases() -> list[ParamTestCase]:
    """Get multi-turn conversation cases."""
    return get_cases_by_category("multi_turn")


def get_partial_cases() -> list[ParamTestCase]:
    """Get partial info cases (no submission expected)."""
    return get_cases_by_category("partial_no_submit")


def get_invalid_cases() -> list[ParamTestCase]:
    """Get invalid input cases."""
    return get_cases_by_category("invalid")


def get_extraction_cases() -> list[ParamTestCase]:
    """Get all cases where extraction is expected (complete + multi_turn)."""
    return [tc for tc in PARAM_TEST_CASES if tc.expected_params is not None]
