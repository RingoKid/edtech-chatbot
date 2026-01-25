"""
Test dataset for routing agent evaluation.

This is the source of truth for routing agent test cases.
Can be synced to Langfuse dataset 'routing-agent-eval' for production evals.
"""

from dataclasses import dataclass
from typing import Union, List, Dict


@dataclass
class RoutingTestCase:
    """
    A single test case for routing agent evaluation.

    Attributes:
        input: User message(s) - either a single string or list of message dicts
        expected_task_type: Expected routing destination (handwriting, vocabulary, idea_generation, or None for greetings)
        expected_max_turns: Maximum turns to complete routing
        description: Human-readable description of the test case
        category: Test category for grouping
    """
    input: Union[str, List[Dict[str, str]]]
    expected_task_type: str | None
    expected_max_turns: int
    description: str
    category: str


# --- Test Cases ---

ROUTING_TEST_CASES: List[RoutingTestCase] = [
    # ==========================================
    # Category: Clear intent - Handwriting (4)
    # ==========================================
    RoutingTestCase(
        input="I want to create a handwriting lesson",
        expected_task_type="handwriting",
        expected_max_turns=1,
        description="Direct request for handwriting lesson",
        category="clear_intent_handwriting",
    ),
    RoutingTestCase(
        input="Help me teach letter A",
        expected_task_type="handwriting",
        expected_max_turns=1,
        description="Letter-specific request implies handwriting",
        category="clear_intent_handwriting",
    ),
    RoutingTestCase(
        input="letter formation practice",
        expected_task_type="handwriting",
        expected_max_turns=1,
        description="Letter formation keyword",
        category="clear_intent_handwriting",
    ),
    RoutingTestCase(
        input="tracing letters for preschool",
        expected_task_type="handwriting",
        expected_max_turns=1,
        description="Tracing letters is handwriting-related",
        category="clear_intent_handwriting",
    ),

    # ==========================================
    # Category: Clear intent - Vocabulary (4)
    # ==========================================
    RoutingTestCase(
        input="I need vocabulary words for my class",
        expected_task_type="vocabulary",
        expected_max_turns=1,
        description="Direct vocabulary request",
        category="clear_intent_vocabulary",
    ),
    RoutingTestCase(
        input="word lists for PreK students",
        expected_task_type="vocabulary",
        expected_max_turns=1,
        description="Word list implies vocabulary",
        category="clear_intent_vocabulary",
    ),
    RoutingTestCase(
        input="vocab lesson for preschoolers",
        expected_task_type="vocabulary",
        expected_max_turns=1,
        description="Vocab abbreviation",
        category="clear_intent_vocabulary",
    ),
    RoutingTestCase(
        input="teaching new words to my students",
        expected_task_type="vocabulary",
        expected_max_turns=1,
        description="Teaching words implies vocabulary",
        category="clear_intent_vocabulary",
    ),

    # ==========================================
    # Category: Clear intent - Idea Generation (4)
    # ==========================================
    RoutingTestCase(
        input="give me some lesson ideas",
        expected_task_type="idea_generation",
        expected_max_turns=1,
        description="Direct idea request",
        category="clear_intent_idea_generation",
    ),
    RoutingTestCase(
        input="brainstorm activities for my classroom",
        expected_task_type="idea_generation",
        expected_max_turns=1,
        description="Brainstorm keyword",
        category="clear_intent_idea_generation",
    ),
    RoutingTestCase(
        input="I'm looking for creative lesson concepts",
        expected_task_type="idea_generation",
        expected_max_turns=1,
        description="Creative concepts implies brainstorming",
        category="clear_intent_idea_generation",
    ),
    RoutingTestCase(
        input="brainstorm some classroom activities for me",
        expected_task_type="idea_generation",
        expected_max_turns=1,
        description="Brainstorm activities request",
        category="clear_intent_idea_generation",
    ),

    # ==========================================
    # Category: Ambiguous (needs clarification) (3)
    # ==========================================
    RoutingTestCase(
        input="help me teach",
        expected_task_type=None,  # Should ask for clarification
        expected_max_turns=1,
        description="Ambiguous - could be any task type",
        category="ambiguous",
    ),
    RoutingTestCase(
        input="make a lesson",
        expected_task_type=None,  # Should ask for clarification
        expected_max_turns=1,
        description="Generic lesson request",
        category="ambiguous",
    ),
    RoutingTestCase(
        input="I need help with my preschool class",
        expected_task_type=None,  # Should ask for clarification
        expected_max_turns=1,
        description="General help request",
        category="ambiguous",
    ),

    # ==========================================
    # Category: Greetings (2)
    # ==========================================
    RoutingTestCase(
        input="hi",
        expected_task_type=None,  # Should greet and ask what they need
        expected_max_turns=1,
        description="Simple greeting",
        category="greeting",
    ),
    RoutingTestCase(
        input="hello there! how are you?",
        expected_task_type=None,  # Should greet and ask what they need
        expected_max_turns=1,
        description="Friendly greeting with question",
        category="greeting",
    ),
]


def get_test_cases_by_category(category: str) -> List[RoutingTestCase]:
    """Get all test cases for a specific category."""
    return [tc for tc in ROUTING_TEST_CASES if tc.category == category]


def get_all_test_cases() -> List[RoutingTestCase]:
    """Get all test cases."""
    return ROUTING_TEST_CASES


def get_clear_intent_cases() -> List[RoutingTestCase]:
    """Get all test cases with clear routing intent."""
    return [tc for tc in ROUTING_TEST_CASES if tc.expected_task_type is not None]
