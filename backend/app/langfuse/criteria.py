"""Evaluation criteria - rule-based evaluators for lesson outputs."""

import re
from dataclasses import dataclass


@dataclass
class EvalResult:
    """Result of an evaluation criterion."""
    name: str
    score: float  # 0.0 to 1.0
    details: dict


# Registry of available criteria
CRITERIA_REGISTRY: dict[str, dict] = {
    "structure_complete": {
        "type": "rule-based",
        "description": "Checks if lesson has all required sections and markers",
    },
    "routing_accuracy": {
        "type": "rule-based",
        "description": "Checks if agent routed to the correct task type",
    },
    "turn_efficiency": {
        "type": "rule-based",
        "description": "Measures how many turns to complete routing (lower is better)",
    },
    "param_extraction_accuracy": {
        "type": "rule-based",
        "description": "Checks if all extracted params match expected (exact match)",
    },
}


def get_available_criteria() -> dict[str, dict]:
    """Get all available evaluation criteria."""
    return CRITERIA_REGISTRY.copy()


def evaluate_structure_complete(output: str) -> EvalResult:
    """
    Check if lesson output contains required sections and markers.

    Required Sections:
    - Standards, Objectives, Materials, Review & Connect,
    - Model, Explain & Engage, Guided Practice, Application, Wrap-Up

    Required Markers:
    - [...]  - AI explains lesson parts
    - #      - Teacher script (what teacher says)
    - (...)  - Child response (expected responses)
    - {...}  - Teacher does (teacher actions)
    - +      - Gesture (phoneme gesture)
    - ##     - Verbal cues (letter formation)
    - *      - Modification (end-of-lesson prompt)

    Returns score as passed_checks / total_checks
    """
    # Required sections (case-insensitive search)
    required_sections = [
        "standards",
        "objectives",
        "materials",
        "review & connect",
        "model, explain & engage",
        "guided practice",
        "application",
        "wrap-up",
    ]

    # Required markers with their patterns
    required_markers = {
        "explanation": r"\[.+?\]",      # [...]
        "teacher_script": r"#[^#]",      # # but not ##
        "child_response": r"\(.+?\)",    # (...)
        "teacher_does": r"\{.+?\}",      # {...}
        "gesture": r"\+",                # +
        "verbal_cues": r"##",            # ##
        "modification": r"\*",           # *
    }

    output_lower = output.lower()
    checks = {}

    # Check sections
    for section in required_sections:
        key = f"section_{section.replace(' ', '_').replace(',', '').replace('&', 'and')}"
        checks[key] = section in output_lower

    # Check markers
    for marker_name, pattern in required_markers.items():
        checks[f"marker_{marker_name}"] = bool(re.search(pattern, output))

    # Calculate score
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    score = passed / total if total > 0 else 0.0

    return EvalResult(
        name="structure_complete",
        score=score,
        details={
            "passed": passed,
            "total": total,
            "checks": checks,
        },
    )


def evaluate_routing_accuracy(
    actual_task_type: str | None,
    expected_task_type: str | None,
) -> EvalResult:
    """
    Evaluate if routing was correct.

    Args:
        actual_task_type: The task type the agent routed to
        expected_task_type: The expected task type

    Returns:
        EvalResult with score 1.0 if correct, 0.0 if incorrect
    """
    is_correct = actual_task_type == expected_task_type
    return EvalResult(
        name="routing_accuracy",
        score=1.0 if is_correct else 0.0,
        details={
            "actual": actual_task_type,
            "expected": expected_task_type,
            "correct": is_correct,
        },
    )


def evaluate_turn_efficiency(
    actual_turns: int,
    expected_max_turns: int,
) -> EvalResult:
    """
    Evaluate turn efficiency.

    Score is 1.0 if within expected turns, scaled down if over.

    Args:
        actual_turns: Number of turns taken
        expected_max_turns: Maximum expected turns

    Returns:
        EvalResult with efficiency score
    """
    if actual_turns <= expected_max_turns:
        score = 1.0
    else:
        # Penalize for extra turns (0.2 penalty per extra turn)
        extra_turns = actual_turns - expected_max_turns
        score = max(0.0, 1.0 - (extra_turns * 0.2))

    return EvalResult(
        name="turn_efficiency",
        score=score,
        details={
            "actual_turns": actual_turns,
            "expected_max_turns": expected_max_turns,
            "within_limit": actual_turns <= expected_max_turns,
        },
    )


def evaluate_param_extraction_accuracy(
    actual_params: dict | None,
    expected_params: dict | None,
) -> EvalResult:
    """
    Evaluate if parameter extraction was correct (exact match).

    All fields must match for a score of 1.0.

    Args:
        actual_params: The extracted parameters (dict with grade, letter, student_level)
        expected_params: The expected parameters

    Returns:
        EvalResult with score 1.0 if all fields match, 0.0 otherwise
    """
    if actual_params is None and expected_params is None:
        # Both None is a match (e.g., for cases where no extraction expected)
        return EvalResult(
            name="param_extraction_accuracy",
            score=1.0,
            details={"actual": None, "expected": None, "correct": True},
        )

    if actual_params is None or expected_params is None:
        # One is None, one isn't - not a match
        return EvalResult(
            name="param_extraction_accuracy",
            score=0.0,
            details={
                "actual": actual_params,
                "expected": expected_params,
                "correct": False,
                "reason": "One is None, other is not",
            },
        )

    # Compare each field
    mismatches = []
    for key in ["grade", "letter", "student_level"]:
        actual_val = actual_params.get(key)
        expected_val = expected_params.get(key)
        # Normalize letter comparison (case-insensitive)
        if key == "letter":
            actual_val = actual_val.upper() if actual_val else None
            expected_val = expected_val.upper() if expected_val else None
        if actual_val != expected_val:
            mismatches.append(f"{key}: got '{actual_val}', expected '{expected_val}'")

    is_correct = len(mismatches) == 0
    return EvalResult(
        name="param_extraction_accuracy",
        score=1.0 if is_correct else 0.0,
        details={
            "actual": actual_params,
            "expected": expected_params,
            "correct": is_correct,
            "mismatches": mismatches,
        },
    )


def run_criterion(criterion_name: str, output: str = "", **kwargs) -> EvalResult | None:
    """
    Run a single evaluation criterion on the output.

    Args:
        criterion_name: Name of the criterion (from CRITERIA_REGISTRY)
        output: Model output text to evaluate (for text-based criteria)
        **kwargs: Additional arguments for specific criteria

    Returns:
        EvalResult or None if criterion not found
    """
    if criterion_name == "structure_complete":
        return evaluate_structure_complete(output)

    if criterion_name == "routing_accuracy":
        return evaluate_routing_accuracy(
            actual_task_type=kwargs.get("actual_task_type"),
            expected_task_type=kwargs.get("expected_task_type"),
        )

    if criterion_name == "turn_efficiency":
        return evaluate_turn_efficiency(
            actual_turns=kwargs.get("actual_turns", 0),
            expected_max_turns=kwargs.get("expected_max_turns", 1),
        )

    if criterion_name == "param_extraction_accuracy":
        return evaluate_param_extraction_accuracy(
            actual_params=kwargs.get("actual_params"),
            expected_params=kwargs.get("expected_params"),
        )

    return None
