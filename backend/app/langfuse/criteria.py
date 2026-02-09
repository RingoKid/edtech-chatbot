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
    "verbatim_check": {
        "type": "rule-based",
        "description": "Checks if [Explanation] text matches Form B exactly",
    },
    "verbal_cues_correct": {
        "type": "rule-based",
        "description": "Checks if ##Sequence Verbal Cues match Form F for target letter",
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
    "vocab_param_extraction_accuracy": {
        "type": "rule-based",
        "description": "Checks if vocabulary params match expected (exact match)",
    },
    "idea_param_extraction_accuracy": {
        "type": "rule-based",
        "description": "Checks if idea generation params match expected (exact match)",
    },
    "scaffolding_within_activity": {
        "type": "llm-judge",
        "description": "Checks if activities within each section are ordered easier -> harder",
    },
    "scaffolding_between_activity": {
        "type": "llm-judge",
        "description": "Checks if activities across sections build on earlier skills",
    },
    "scaffolding_gradual_release": {
        "type": "llm-judge",
        "description": "Checks if teacher support decreases across the lesson (I do → We do → You do)",
    },
    "scaffolding_decomposition": {
        "type": "llm-judge",
        "description": "Checks if complex tasks have prerequisite sub-skills taught in earlier sections",
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


# Expected verbatim explanations from Form B (must match exactly)
EXPECTED_EXPLANATIONS = {
    "review_connect": (
        "The purpose of this part of the lesson is to start with a quick review of "
        "previously learned sounds. Do not use sounds that have not been directly taught. "
        "Do not use words that have sounds that have not been directly taught."
    ),
    "model_explain_engage": (
        "The purpose of this part of the lesson is to connect a sound or sound patterns "
        "that you focused on during your reading block to writing its corresponding "
        "grapheme patterns. First, make sure children clearly can distinguish the targeted "
        "sound; then, hook that sound to the letter patterns through modeling and explaining "
        "the sequence of strokes for letters and correct order of letters."
    ),
    "guided_practice": (
        "The purpose of this part of the lesson is to give children practice writing the "
        "letter while supporting proper pencil grip and correct sequence of stroke formation "
        "using handwriting lines."
    ),
    "application": (
        "The purpose of this part of the lesson is to facilitate children's spelling of the "
        "letter or letter patterns when they hear the sound(s). This supports children's "
        "early coordination of matching sound to letter(s) for the purpose of spelling words"
    ),
    "wrap_up": (
        "The purpose of this part of the lesson is to remind students what they were focused "
        "on and provide praise for their accomplishments"
    ),
}


# Verbal cues from Form F for each letter (uppercase)
VERBAL_CUES = {
    "A": "Big line up, big line down, little line across",
    "B": "Big line down, rainbow bump, rainbow bump",
    "C": "Start at the top, curve around like a rainbow",
    "D": "Big line down, big rainbow bump",
    "E": "Big line down, little line at the top, middle, and bottom",
    "F": "Big line down, little line at the top and in the middle",
    "G": "Big curve like a rainbow, little line in",
    "H": "Big line down, big line down, little line across",
    "I": "Little line on top, big line down, little line on bottom",
    "J": "Big line down and hook, little line on top",
    "K": "Big line down, little line slant in, little line slant out",
    "L": "Big line down, little line across",
    "M": "Big line down, rainbow bump, rainbow bump",
    "N": "Big line down, slant up, big line down",
    "O": "Big curve around, close it up",
    "P": "Big line down, rainbow bump",
    "Q": "Big curve around, close it up, little line out",
    "R": "Big line down, rainbow bump, slant out",
    "S": "Little curve this way, little curve that way",
    "T": "Big line down, little line across the top",
    "U": "Big curve down and up, little line down",
    "V": "Slant down, slant up",
    "W": "Slant down, slant up, slant down, slant up",
    "X": "Slant down, slant the other way",
    "Y": "Little slant, little slant, big line down",
    "Z": "Little line across, slant down, little line across",
    # Lowercase
    "a": "Start at the middle, rainbow around, little line down",
    "b": "Big line down, rainbow bump from the middle",
    "c": "Start at the middle, curve around like a rainbow",
    "d": "Rainbow around, big line up and down",
    "e": "Little line out, curve around like a smile",
    "f": "Curve down, straight down, little line across",
    "g": "Rainbow around, little line down, hook under",
    "h": "Big line down, rainbow bump from the middle",
    "i": "Little line down, dot on top",
    "j": "Little line down, hook it up, dot on top",
    "k": "Big line down, little slant in, little slant out",
    "l": "Big line down",
    "m": "Little line down, rainbow bump, rainbow bump",
    "n": "Little line down, rainbow bump",
    "o": "Rainbow around, close it up",
    "p": "Big line down below the bottom, rainbow bump",
    "q": "Rainbow around, little line down, slant out",
    "r": "Little line down, tiny curve out",
    "s": "Little curve this way, little curve that way",
    "t": "Little line down, little line across the top",
    "u": "Curve down, curve up, little line down",
    "v": "Slant down, slant up",
    "w": "Slant down, slant up, slant down, slant up",
    "x": "Slant down, slant the other way",
    "y": "Slant down, slant down below the line",
    "z": "Little line across, slant down the stairs, little line across",
}


def evaluate_verbatim_check(output: str) -> EvalResult:
    """
    Check if [Explanation] text matches Form B exactly.

    Extracts text within brackets [...] and compares against expected
    verbatim explanations from Form B.

    Returns score as matched_explanations / total_expected.
    """
    # Extract all [Explanation] blocks from output
    # Match content within brackets, handling multi-line
    explanation_pattern = r'\[([^\]]+)\]'
    found_explanations = re.findall(explanation_pattern, output, re.IGNORECASE | re.DOTALL)

    # Normalize text for comparison (lowercase, collapse whitespace)
    def normalize(text: str) -> str:
        return ' '.join(text.lower().split())

    # Check each expected explanation
    checks = {}
    for key, expected in EXPECTED_EXPLANATIONS.items():
        expected_norm = normalize(expected)
        found = False

        for found_exp in found_explanations:
            found_norm = normalize(found_exp)
            # Check if expected text is contained in found text
            # (allow some flexibility for surrounding context)
            if expected_norm in found_norm or found_norm in expected_norm:
                found = True
                break
            # Also check for high similarity (80%+ overlap)
            # using simple word overlap
            expected_words = set(expected_norm.split())
            found_words = set(found_norm.split())
            if len(expected_words) > 0:
                overlap = len(expected_words & found_words) / len(expected_words)
                if overlap >= 0.8:
                    found = True
                    break

        checks[key] = found

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    score = passed / total if total > 0 else 0.0

    return EvalResult(
        name="verbatim_check",
        score=score,
        details={
            "passed": passed,
            "total": total,
            "checks": checks,
            "found_explanations": len(found_explanations),
        },
    )


def evaluate_verbal_cues_correct(output: str, target_letter: str) -> EvalResult:
    """
    Check if ##Sequence Verbal Cues match Form F for target letter.

    Extracts verbal cues after ## markers and compares against expected
    cues for the target letter.

    Args:
        output: The lesson output text
        target_letter: The target letter (A-Z or a-z)

    Returns:
        EvalResult with score 1.0 if cues match, 0.0 otherwise
    """
    # Get expected cues for target letter
    letter_upper = target_letter.upper()
    letter_lower = target_letter.lower()

    expected_upper = VERBAL_CUES.get(letter_upper, "")
    expected_lower = VERBAL_CUES.get(letter_lower, "")

    # Extract ##Sequence Verbal Cues section
    # Look for content after ## that mentions verbal cues
    cue_pattern = r'##\s*(?:Sequence\s+)?Verbal\s+Cues[:\s]*([^\n#]+(?:\n(?!#)[^\n]+)*)'
    matches = re.findall(cue_pattern, output, re.IGNORECASE)

    if not matches:
        # Try alternative pattern - just look for ## followed by cue text
        alt_pattern = r'##\s*([^\n]+)'
        matches = re.findall(alt_pattern, output)

    # Normalize for comparison
    def normalize(text: str) -> str:
        return ' '.join(text.lower().strip().split())

    expected_upper_norm = normalize(expected_upper)
    expected_lower_norm = normalize(expected_lower)

    found_match = False
    matched_cue = None
    for match in matches:
        match_norm = normalize(match)
        # Check if expected cues appear in the match
        if expected_upper_norm and expected_upper_norm in match_norm:
            found_match = True
            matched_cue = match.strip()
            break
        if expected_lower_norm and expected_lower_norm in match_norm:
            found_match = True
            matched_cue = match.strip()
            break
        # Check word overlap
        expected_words = set(expected_upper_norm.split()) | set(expected_lower_norm.split())
        match_words = set(match_norm.split())
        if len(expected_words) > 0:
            overlap = len(expected_words & match_words) / len(expected_words)
            if overlap >= 0.7:
                found_match = True
                matched_cue = match.strip()
                break

    return EvalResult(
        name="verbal_cues_correct",
        score=1.0 if found_match else 0.0,
        details={
            "target_letter": target_letter,
            "expected_uppercase": expected_upper,
            "expected_lowercase": expected_lower,
            "matched_cue": matched_cue,
            "found_match": found_match,
            "cue_matches_found": len(matches),
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


def evaluate_vocab_param_extraction_accuracy(
    actual_params: dict | None,
    expected_params: dict | None,
) -> EvalResult:
    """
    Evaluate if vocabulary parameter extraction was correct.

    Compares: grade, writing_type, key_vocabulary, objectives, student_level

    Args:
        actual_params: The extracted vocabulary parameters
        expected_params: The expected parameters

    Returns:
        EvalResult with score 1.0 if all fields match, 0.0 otherwise
    """
    if actual_params is None and expected_params is None:
        return EvalResult(
            name="vocab_param_extraction_accuracy",
            score=1.0,
            details={"actual": None, "expected": None, "correct": True},
        )

    if actual_params is None or expected_params is None:
        return EvalResult(
            name="vocab_param_extraction_accuracy",
            score=0.0,
            details={
                "actual": actual_params,
                "expected": expected_params,
                "correct": False,
                "reason": "One is None, other is not",
            },
        )

    mismatches = []
    for key in ["grade", "writing_type", "objectives", "student_level"]:
        actual_val = actual_params.get(key)
        expected_val = expected_params.get(key)
        if actual_val != expected_val:
            mismatches.append(f"{key}: got '{actual_val}', expected '{expected_val}'")

    # Special handling for key_vocabulary (list comparison - order doesn't matter)
    actual_vocab = set(actual_params.get("key_vocabulary", []))
    expected_vocab = set(expected_params.get("key_vocabulary", []))
    if actual_vocab != expected_vocab:
        mismatches.append(f"key_vocabulary: got {actual_vocab}, expected {expected_vocab}")

    is_correct = len(mismatches) == 0
    return EvalResult(
        name="vocab_param_extraction_accuracy",
        score=1.0 if is_correct else 0.0,
        details={
            "actual": actual_params,
            "expected": expected_params,
            "correct": is_correct,
            "mismatches": mismatches,
        },
    )


def evaluate_idea_param_extraction_accuracy(
    actual_params: dict | None,
    expected_params: dict | None,
) -> EvalResult:
    """
    Evaluate if idea generation parameter extraction was correct.

    Compares: grade, genre, genre_component, writing_stage, objectives, student_level

    Args:
        actual_params: The extracted idea generation parameters
        expected_params: The expected parameters

    Returns:
        EvalResult with score 1.0 if all fields match, 0.0 otherwise
    """
    if actual_params is None and expected_params is None:
        return EvalResult(
            name="idea_param_extraction_accuracy",
            score=1.0,
            details={"actual": None, "expected": None, "correct": True},
        )

    if actual_params is None or expected_params is None:
        return EvalResult(
            name="idea_param_extraction_accuracy",
            score=0.0,
            details={
                "actual": actual_params,
                "expected": expected_params,
                "correct": False,
                "reason": "One is None, other is not",
            },
        )

    mismatches = []
    for key in ["grade", "genre", "genre_component", "writing_stage", "objectives", "student_level"]:
        actual_val = actual_params.get(key)
        expected_val = expected_params.get(key)
        if actual_val != expected_val:
            mismatches.append(f"{key}: got '{actual_val}', expected '{expected_val}'")

    is_correct = len(mismatches) == 0
    return EvalResult(
        name="idea_param_extraction_accuracy",
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

    if criterion_name == "verbatim_check":
        return evaluate_verbatim_check(output)

    if criterion_name == "verbal_cues_correct":
        return evaluate_verbal_cues_correct(
            output=output,
            target_letter=kwargs.get("target_letter", "A"),
        )

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
