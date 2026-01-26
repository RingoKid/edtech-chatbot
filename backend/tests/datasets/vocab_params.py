"""
Test dataset for vocabulary parameter collection agent evaluation.

This is the source of truth for vocabulary param agent test cases.
Can be synced to Langfuse dataset for production evals.
"""

from dataclasses import dataclass
from typing import Union, List, Dict, Optional


@dataclass
class VocabParamTestCase:
    """
    A single test case for vocabulary param agent evaluation.

    Attributes:
        input: User message(s) - either a single string or list of message dicts
        task_type: The task type from routing (always "vocabulary")
        expected_params: Expected extracted parameters (or None if params shouldn't be extracted)
        description: Human-readable description of the test case
        category: Test category for grouping
    """
    input: Union[str, List[Dict[str, str]]]
    task_type: str
    expected_params: Optional[Dict[str, any]]
    description: str
    category: str


# --- Test Cases ---

VOCAB_TEST_CASES: List[VocabParamTestCase] = [
    # ==========================================
    # Category: All params in one message (4)
    # ==========================================
    VocabParamTestCase(
        input="PreK informational writing, vocabulary words: ocean, fish, water. Objectives: be-verbs",
        task_type="vocabulary",
        expected_params={
            "grade": "PreK",
            "writing_type": "informational",
            "key_vocabulary": ["ocean", "fish", "water"],
            "objectives": "be-verbs",
            "student_level": "on-level",
        },
        description="All params: PreK informational with vocab list",
        category="complete",
    ),
    VocabParamTestCase(
        input="K narrative writing unit. Words: happy, sad, friend. Focus on prepositional phrases.",
        task_type="vocabulary",
        expected_params={
            "grade": "K",
            "writing_type": "narrative",
            "key_vocabulary": ["happy", "sad", "friend"],
            "objectives": "prepositional phrases",
            "student_level": "on-level",
        },
        description="All params: K narrative with objectives",
        category="complete",
    ),
    VocabParamTestCase(
        input="1st grade opinion writing, key words are fair, unfair, because. We're working on sentence starters.",
        task_type="vocabulary",
        expected_params={
            "grade": "1st",
            "writing_type": "opinion",
            "key_vocabulary": ["fair", "unfair", "because"],
            "objectives": "sentence starters",
            "student_level": "on-level",
        },
        description="All params: 1st grade opinion",
        category="complete",
    ),
    VocabParamTestCase(
        input="PreK personal narrative, vocabulary: family, love, home. Objective is action verbs.",
        task_type="vocabulary",
        expected_params={
            "grade": "PreK",
            "writing_type": "personal_narrative",
            "key_vocabulary": ["family", "love", "home"],
            "objectives": "action verbs",
            "student_level": "on-level",
        },
        description="All params: PreK personal narrative",
        category="complete",
    ),

    # ==========================================
    # Category: Missing grade (2)
    # ==========================================
    VocabParamTestCase(
        input="informational writing, words: plant, grow, seed. Focus on adjectives.",
        task_type="vocabulary",
        expected_params=None,  # Should ask for grade
        description="Missing grade: informational with vocab",
        category="missing_grade",
    ),
    VocabParamTestCase(
        input="narrative unit with vocabulary dog, cat, pet and working on verbs",
        task_type="vocabulary",
        expected_params=None,  # Should ask for grade
        description="Missing grade: narrative with vocab",
        category="missing_grade",
    ),

    # ==========================================
    # Category: Missing writing type (2)
    # ==========================================
    VocabParamTestCase(
        input="PreK vocabulary lesson with words: big, small, tiny. Objectives: size words.",
        task_type="vocabulary",
        expected_params=None,  # Should ask for writing type
        description="Missing writing type: PreK with vocab",
        category="missing_writing_type",
    ),
    VocabParamTestCase(
        input="K level, key words are run, jump, play. Working on action verbs.",
        task_type="vocabulary",
        expected_params=None,  # Should ask for writing type
        description="Missing writing type: K with vocab",
        category="missing_writing_type",
    ),

    # ==========================================
    # Category: Missing vocabulary words (2)
    # ==========================================
    VocabParamTestCase(
        input="PreK informational writing. Focus on be-verbs.",
        task_type="vocabulary",
        expected_params=None,  # Should ask for vocabulary
        description="Missing vocabulary: PreK informational",
        category="missing_vocabulary",
    ),
    VocabParamTestCase(
        input="1st grade opinion writing unit, working on transition words",
        task_type="vocabulary",
        expected_params=None,  # Should ask for vocabulary
        description="Missing vocabulary: 1st opinion",
        category="missing_vocabulary",
    ),

    # ==========================================
    # Category: Missing objectives (2)
    # ==========================================
    VocabParamTestCase(
        input="PreK narrative, vocabulary words: princess, castle, dragon",
        task_type="vocabulary",
        expected_params=None,  # Should ask for objectives
        description="Missing objectives: PreK narrative",
        category="missing_objectives",
    ),
    VocabParamTestCase(
        input="K informational writing with words weather, rain, sun",
        task_type="vocabulary",
        expected_params=None,  # Should ask for objectives
        description="Missing objectives: K informational",
        category="missing_objectives",
    ),

    # ==========================================
    # Category: With student level specified (2)
    # ==========================================
    VocabParamTestCase(
        input="PreK narrative, words: bear, forest, honey. Objectives: describing words. For struggling students.",
        task_type="vocabulary",
        expected_params={
            "grade": "PreK",
            "writing_type": "narrative",
            "key_vocabulary": ["bear", "forest", "honey"],
            "objectives": "describing words",
            "student_level": "struggling",
        },
        description="With level: struggling students",
        category="with_level",
    ),
    VocabParamTestCase(
        input="1st grade opinion, vocab: better, worse, prefer. Focus on comparison words. Advanced level.",
        task_type="vocabulary",
        expected_params={
            "grade": "1st",
            "writing_type": "opinion",
            "key_vocabulary": ["better", "worse", "prefer"],
            "objectives": "comparison words",
            "student_level": "advanced",
        },
        description="With level: advanced level",
        category="with_level",
    ),

    # ==========================================
    # Category: Invalid inputs (2)
    # ==========================================
    VocabParamTestCase(
        input="3rd grade informational, words: ecosystem, habitat. Objectives: scientific vocabulary.",
        task_type="vocabulary",
        expected_params=None,  # Should explain valid grades
        description="Invalid: 3rd grade not valid",
        category="invalid",
    ),
    VocabParamTestCase(
        input="PreK poetry writing, words: rhyme, verse. Objectives: rhythm.",
        task_type="vocabulary",
        expected_params=None,  # Should explain valid writing types
        description="Invalid: poetry not a valid writing type",
        category="invalid",
    ),

    # ==========================================
    # Category: Edge cases (2)
    # ==========================================
    VocabParamTestCase(
        input="prek INFORMATIONAL, vocab: red, blue, green, yellow. objective: color words",
        task_type="vocabulary",
        expected_params={
            "grade": "PreK",
            "writing_type": "informational",
            "key_vocabulary": ["red", "blue", "green", "yellow"],
            "objectives": "color words",
            "student_level": "on-level",
        },
        description="Edge: case insensitive inputs",
        category="edge",
    ),
    VocabParamTestCase(
        input="K, narrative, just one word: adventure, and we're doing descriptive language",
        task_type="vocabulary",
        expected_params={
            "grade": "K",
            "writing_type": "narrative",
            "key_vocabulary": ["adventure"],
            "objectives": "descriptive language",
            "student_level": "on-level",
        },
        description="Edge: single vocabulary word",
        category="edge",
    ),
]


def get_test_cases_by_category(category: str) -> List[VocabParamTestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in VOCAB_TEST_CASES if tc.category == category]


def get_all_test_cases() -> List[VocabParamTestCase]:
    """Get all test cases."""
    return VOCAB_TEST_CASES


def get_extraction_cases() -> List[VocabParamTestCase]:
    """Get all test cases where param extraction is expected."""
    return [tc for tc in VOCAB_TEST_CASES if tc.expected_params is not None]


def get_clarification_cases() -> List[VocabParamTestCase]:
    """Get all test cases where clarification is expected (no extraction)."""
    return [tc for tc in VOCAB_TEST_CASES if tc.expected_params is None]
