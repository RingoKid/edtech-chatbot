"""
Test dataset for idea generation parameter collection agent evaluation.

This is the source of truth for idea generation param agent test cases.
Can be synced to Langfuse dataset for production evals.
"""

from dataclasses import dataclass
from typing import Union, List, Dict, Optional


@dataclass
class IdeaParamTestCase:
    """
    A single test case for idea generation param agent evaluation.

    Attributes:
        input: User message(s) - either a single string or list of message dicts
        task_type: The task type from routing (always "idea_generation")
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

IDEA_TEST_CASES: List[IdeaParamTestCase] = [
    # ==========================================
    # Category: All params in one message (4)
    # ==========================================
    IdeaParamTestCase(
        input="PreK narrative, focus on topic sentence, brainstorm stage, objectives: generating story ideas",
        task_type="idea_generation",
        expected_params={
            "grade": "PreK",
            "genre": "narrative",
            "genre_component": "topic sentence",
            "writing_stage": "brainstorm",
            "objectives": "generating story ideas",
            "student_level": "on-level",
        },
        description="All params: PreK narrative brainstorm",
        category="complete",
    ),
    IdeaParamTestCase(
        input="K informational writing, working on relevant details, initial draft stage. Objective: organizing information",
        task_type="idea_generation",
        expected_params={
            "grade": "K",
            "genre": "informational",
            "genre_component": "relevant details",
            "writing_stage": "initial_draft",
            "objectives": "organizing information",
            "student_level": "on-level",
        },
        description="All params: K informational initial draft",
        category="complete",
    ),
    IdeaParamTestCase(
        input="1st grade opinion, focusing on supporting reasons, revise stage, objectives: strengthening arguments",
        task_type="idea_generation",
        expected_params={
            "grade": "1st",
            "genre": "opinion",
            "genre_component": "supporting reasons",
            "writing_stage": "revise",
            "objectives": "strengthening arguments",
            "student_level": "on-level",
        },
        description="All params: 1st opinion revise",
        category="complete",
    ),
    IdeaParamTestCase(
        input="PreK narrative genre, character development component, edit stage, objective is checking for capitals",
        task_type="idea_generation",
        expected_params={
            "grade": "PreK",
            "genre": "narrative",
            "genre_component": "character development",
            "writing_stage": "edit",
            "objectives": "checking for capitals",
            "student_level": "on-level",
        },
        description="All params: PreK narrative edit",
        category="complete",
    ),

    # ==========================================
    # Category: Missing grade (2)
    # ==========================================
    IdeaParamTestCase(
        input="narrative genre, topic sentence, brainstorm stage, generating ideas",
        task_type="idea_generation",
        expected_params=None,  # Should ask for grade
        description="Missing grade: narrative brainstorm",
        category="missing_grade",
    ),
    IdeaParamTestCase(
        input="informational writing, relevant details focus, initial draft, objectives: fact gathering",
        task_type="idea_generation",
        expected_params=None,  # Should ask for grade
        description="Missing grade: informational initial draft",
        category="missing_grade",
    ),

    # ==========================================
    # Category: Missing genre (2)
    # ==========================================
    IdeaParamTestCase(
        input="PreK, working on topic sentence, brainstorm stage, objectives: idea generation",
        task_type="idea_generation",
        expected_params=None,  # Should ask for genre
        description="Missing genre: PreK brainstorm",
        category="missing_genre",
    ),
    IdeaParamTestCase(
        input="K level, focus is relevant details, revise stage, organizing thoughts",
        task_type="idea_generation",
        expected_params=None,  # Should ask for genre
        description="Missing genre: K revise",
        category="missing_genre",
    ),

    # ==========================================
    # Category: Missing genre component (2)
    # ==========================================
    IdeaParamTestCase(
        input="PreK narrative, brainstorm stage, objectives: coming up with ideas",
        task_type="idea_generation",
        expected_params=None,  # Should ask for genre component
        description="Missing component: PreK narrative brainstorm",
        category="missing_component",
    ),
    IdeaParamTestCase(
        input="1st grade opinion, edit stage, checking spelling and punctuation",
        task_type="idea_generation",
        expected_params=None,  # Should ask for genre component
        description="Missing component: 1st opinion edit",
        category="missing_component",
    ),

    # ==========================================
    # Category: Missing writing stage (2)
    # ==========================================
    IdeaParamTestCase(
        input="PreK informational, focus on relevant details, objectives: fact organization",
        task_type="idea_generation",
        expected_params=None,  # Should ask for writing stage
        description="Missing stage: PreK informational",
        category="missing_stage",
    ),
    IdeaParamTestCase(
        input="K narrative, working on character development, goal is descriptive writing",
        task_type="idea_generation",
        expected_params=None,  # Should ask for writing stage
        description="Missing stage: K narrative",
        category="missing_stage",
    ),

    # ==========================================
    # Category: Missing objectives (2)
    # ==========================================
    IdeaParamTestCase(
        input="PreK narrative, topic sentence component, brainstorm stage",
        task_type="idea_generation",
        expected_params=None,  # Should ask for objectives
        description="Missing objectives: PreK narrative",
        category="missing_objectives",
    ),
    IdeaParamTestCase(
        input="K opinion, supporting reasons, revise stage",
        task_type="idea_generation",
        expected_params=None,  # Should ask for objectives
        description="Missing objectives: K opinion",
        category="missing_objectives",
    ),

    # ==========================================
    # Category: With student level specified (2)
    # ==========================================
    IdeaParamTestCase(
        input="PreK narrative, setting description, brainstorm, objectives: where stories happen. For struggling learners.",
        task_type="idea_generation",
        expected_params={
            "grade": "PreK",
            "genre": "narrative",
            "genre_component": "setting description",
            "writing_stage": "brainstorm",
            "objectives": "where stories happen",
            "student_level": "struggling",
        },
        description="With level: struggling learners",
        category="with_level",
    ),
    IdeaParamTestCase(
        input="1st grade opinion, counterarguments component, revise stage, objectives: considering other views. Advanced students.",
        task_type="idea_generation",
        expected_params={
            "grade": "1st",
            "genre": "opinion",
            "genre_component": "counterarguments",
            "writing_stage": "revise",
            "objectives": "considering other views",
            "student_level": "advanced",
        },
        description="With level: advanced students",
        category="with_level",
    ),

    # ==========================================
    # Category: Invalid inputs (2)
    # ==========================================
    IdeaParamTestCase(
        input="4th grade narrative, plot development, brainstorm, objectives: story arcs",
        task_type="idea_generation",
        expected_params=None,  # Should explain valid grades
        description="Invalid: 4th grade not valid",
        category="invalid",
    ),
    IdeaParamTestCase(
        input="PreK persuasive writing, claims, brainstorm, objectives: convincing others",
        task_type="idea_generation",
        expected_params=None,  # Should explain valid genres (persuasive != opinion)
        description="Invalid: persuasive not a valid genre",
        category="invalid",
    ),

    # ==========================================
    # Category: Edge cases (2)
    # ==========================================
    IdeaParamTestCase(
        input="prek NARRATIVE, TOPIC SENTENCE, BRAINSTORM, generating ideas",
        task_type="idea_generation",
        expected_params={
            "grade": "PreK",
            "genre": "narrative",
            "genre_component": "topic sentence",
            "writing_stage": "brainstorm",
            "objectives": "generating ideas",
            "student_level": "on-level",
        },
        description="Edge: all caps input",
        category="edge",
    ),
    IdeaParamTestCase(
        input="K, informational, details, draft, organizing",
        task_type="idea_generation",
        expected_params={
            "grade": "K",
            "genre": "informational",
            "genre_component": "details",
            "writing_stage": "initial_draft",
            "objectives": "organizing",
            "student_level": "on-level",
        },
        description="Edge: minimal input with abbreviations",
        category="edge",
    ),
]


def get_test_cases_by_category(category: str) -> List[IdeaParamTestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in IDEA_TEST_CASES if tc.category == category]


def get_all_test_cases() -> List[IdeaParamTestCase]:
    """Get all test cases."""
    return IDEA_TEST_CASES


def get_extraction_cases() -> List[IdeaParamTestCase]:
    """Get all test cases where param extraction is expected."""
    return [tc for tc in IDEA_TEST_CASES if tc.expected_params is not None]


def get_clarification_cases() -> List[IdeaParamTestCase]:
    """Get all test cases where clarification is expected (no extraction)."""
    return [tc for tc in IDEA_TEST_CASES if tc.expected_params is None]
