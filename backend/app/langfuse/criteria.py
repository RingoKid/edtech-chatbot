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


def run_criterion(criterion_name: str, output: str) -> EvalResult | None:
    """
    Run a single evaluation criterion on the output.

    Args:
        criterion_name: Name of the criterion (from CRITERIA_REGISTRY)
        output: Model output text to evaluate

    Returns:
        EvalResult or None if criterion not found
    """
    if criterion_name == "structure_complete":
        return evaluate_structure_complete(output)

    return None
