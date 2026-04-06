"""
Run planner directives eval — validates that the activity planner produces
correct directive fields for each grade×level×letter combination.

Unlike the other 14 evals, this one needs NO LLM judge — directive correctness
is deterministic from the spec's mapping tables. It runs the planner live and
checks the ActivityPlan tool call output.

Usage:
    # Run all 10 fixtures
    docker compose exec backend python scripts/run_planner_directives_eval.py

    # Run a specific fixture
    docker compose exec backend python scripts/run_planner_directives_eval.py --fixture k_b_onlevel

    # Verbose mode (show all field checks, not just failures)
    docker compose exec backend python scripts/run_planner_directives_eval.py -v
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime

from langchain_core.messages import HumanMessage

from app.graph.agents.activity_planner import (
    create_activity_planner_agent,
    PLANNER_TOOL_NAME,
)

RESULTS_DIR = "tests/evals/results"

VALID_SPELLING_PATTERNS = {"single_sound", "VC", "CVC", "CVCe", "CCVC", "CVCC"}
VALID_TECHNIQUES = {
    "magic_finger_write", "trace_and_say", "write_and_say",
    "say_and_write", "write_and_sound", "disappearing_letter", "cover_and_try",
}
VALID_INTENSITIES = {"heavy", "moderate", "light"}

# 10 fixtures: 3 grades × 3 levels + extra branch coverage
# Includes vowels for 1st grade to test CVCe vs CVC detection
FIXTURE_PARAMS = [
    # PreK
    {"id": "prek_m_struggling", "grade": "PreK", "letter": "m", "student_level": "struggling",
     "previously_learned": [], "skill_focus": "isolating_sounds"},
    {"id": "prek_s_onlevel", "grade": "PreK", "letter": "s", "student_level": "on-level",
     "previously_learned": ["m", "a"], "skill_focus": "isolating_sounds"},
    {"id": "prek_t_advanced", "grade": "PreK", "letter": "t", "student_level": "advanced",
     "previously_learned": ["m", "a", "s"], "skill_focus": "letter_formation"},
    # K
    {"id": "k_b_struggling", "grade": "K", "letter": "b", "student_level": "struggling",
     "previously_learned": ["m", "a", "s"], "skill_focus": "isolating_sounds"},
    {"id": "k_d_onlevel", "grade": "K", "letter": "d", "student_level": "on-level",
     "previously_learned": ["m", "a", "s", "t", "b"], "skill_focus": "spelling"},
    {"id": "k_w_advanced", "grade": "K", "letter": "w", "student_level": "advanced",
     "previously_learned": ["m", "a", "s", "t", "b", "c", "d"], "skill_focus": "spelling"},
    # 1st — includes vowels to test CVCe vs CVC by level
    {"id": "first_p_struggling", "grade": "1st", "letter": "p", "student_level": "struggling",
     "previously_learned": ["m", "a", "s", "t", "b", "c", "d"], "skill_focus": "spelling"},
    {"id": "first_i_onlevel", "grade": "1st", "letter": "i", "student_level": "on-level",
     "previously_learned": ["a", "c", "d", "m", "p", "s", "t"], "skill_focus": "spelling"},
    {"id": "first_a_struggling", "grade": "1st", "letter": "a", "student_level": "struggling",
     "previously_learned": ["m", "s", "t", "b", "c", "d"], "skill_focus": "spelling"},
    {"id": "first_r_advanced", "grade": "1st", "letter": "r", "student_level": "advanced",
     "previously_learned": ["a", "b", "c", "d", "e", "i", "m", "p", "s", "t"], "skill_focus": "blending"},
]


# ---------------------------------------------------------------------------
# Expected value functions — deterministic rules from spec
# ---------------------------------------------------------------------------

def expected_spelling_pattern(grade: str, letter: str, student_level: str) -> list[str]:
    """Return acceptable spelling_pattern values for the given params."""
    if grade == "PreK":
        return ["single_sound"]
    if grade == "K":
        return ["CVC"]
    # 1st grade
    is_vowel = letter.lower() in "aeiou"
    if is_vowel and student_level in ("on-level", "advanced"):
        return ["CVCe"]
    if is_vowel and student_level == "struggling":
        return ["CVC"]
    # 1st + consonant
    return ["CVC", "CCVC", "CVCC"]


def expected_include_directionality(grade: str, student_level: str) -> bool:
    if grade == "PreK":
        return True
    if grade == "K" and student_level == "struggling":
        return True
    return False


def expected_include_articulation(grade: str) -> bool:
    return grade != "1st"


def expected_guided_practice_techniques(grade: str, student_level: str) -> list[str]:
    """Return the exact expected technique list from the spec table."""
    if grade == "PreK":
        return ["magic_finger_write", "trace_and_say", "write_and_say"]
    if grade == "K":
        if student_level == "struggling":
            return ["magic_finger_write", "trace_and_say", "write_and_say"]
        if student_level == "on-level":
            return ["trace_and_say", "say_and_write", "write_and_say"]
        return ["say_and_write", "write_and_say", "write_and_sound"]  # advanced
    # 1st
    if student_level == "struggling":
        return ["say_and_write", "write_and_say", "write_and_sound"]
    if student_level == "on-level":
        return ["cover_and_try", "say_and_write", "write_and_sound"]
    return ["cover_and_try", "disappearing_letter", "write_and_sound"]  # advanced


def expected_scaffolding_intensity(grade: str, student_level: str) -> str:
    if grade == "PreK":
        return "heavy"
    if grade == "K":
        return "heavy" if student_level == "struggling" else "moderate"
    # 1st
    return "moderate" if student_level == "struggling" else "light"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_directives(plan: dict, params: dict) -> list[dict]:
    """
    Validate each directive field against expected values.

    Returns a list of check results, each with:
      field, expected, actual, passed, note
    """
    grade = params["grade"]
    letter = params["letter"]
    level = params["student_level"]
    results = []

    # 1. spelling_pattern
    sp = plan.get("spelling_pattern", "")
    acceptable = expected_spelling_pattern(grade, letter, level)
    results.append({
        "field": "spelling_pattern",
        "expected": acceptable,
        "actual": sp,
        "passed": sp in acceptable,
        "note": "" if sp in acceptable else f"got '{sp}', expected one of {acceptable}",
    })

    # 2. include_directionality
    dir_val = plan.get("include_directionality")
    exp_dir = expected_include_directionality(grade, level)
    results.append({
        "field": "include_directionality",
        "expected": exp_dir,
        "actual": dir_val,
        "passed": dir_val == exp_dir,
        "note": "" if dir_val == exp_dir else f"got {dir_val}, expected {exp_dir}",
    })

    # 3. include_articulation
    art_val = plan.get("include_articulation")
    exp_art = expected_include_articulation(grade)
    results.append({
        "field": "include_articulation",
        "expected": exp_art,
        "actual": art_val,
        "passed": art_val == exp_art,
        "note": "" if art_val == exp_art else f"got {art_val}, expected {exp_art}",
    })

    # 4. guided_practice_techniques — exact match against spec table
    techniques = plan.get("guided_practice_techniques", [])
    exp_tech = expected_guided_practice_techniques(grade, level)
    tech_match = techniques == exp_tech
    tech_note = ""
    if not isinstance(techniques, list):
        tech_note = "not a list"
    elif not tech_match:
        tech_note = f"got {techniques}, expected {exp_tech}"
    results.append({
        "field": "guided_practice_techniques",
        "expected": exp_tech,
        "actual": techniques,
        "passed": tech_match,
        "note": tech_note,
    })

    # 5. scaffolding_intensity
    si = plan.get("scaffolding_intensity", "")
    exp_si = expected_scaffolding_intensity(grade, level)
    results.append({
        "field": "scaffolding_intensity",
        "expected": exp_si,
        "actual": si,
        "passed": si == exp_si,
        "note": "" if si == exp_si else f"got '{si}', expected '{exp_si}'",
    })

    # 6. content_scope — must be non-empty, 2+ sentences
    scope = plan.get("content_scope", "")
    sentence_ends = scope.count(".") + scope.count("!") + scope.count("?")
    scope_ok = isinstance(scope, str) and len(scope) >= 40 and sentence_ends >= 2
    results.append({
        "field": "content_scope",
        "expected": ">=2 sentences, >=40 chars",
        "actual": f"({len(scope)} chars, {sentence_ends} sentences)" if scope else "(empty)",
        "passed": scope_ok,
        "note": "" if scope_ok else f"too short or too few sentences ({len(scope)} chars, {sentence_ends} sentences)",
    })

    # 7. all fields present (not default fallbacks)
    # If spelling_pattern is missing from tool call, _extract_plan defaults to "CVC"
    # We can detect likely defaults by checking for the combination of all defaults
    all_defaults = (
        sp == "CVC"
        and dir_val is False
        and art_val is True
        and techniques == []
        and si == "moderate"
        and scope == ""
    )
    results.append({
        "field": "all_fields_present",
        "expected": "not all defaults",
        "actual": "all defaults detected" if all_defaults else "fields populated",
        "passed": not all_defaults,
        "note": "planner likely omitted all directive fields" if all_defaults else "",
    })

    return results


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_planner(params: dict) -> dict | None:
    """Run the planner agent and extract the ActivityPlan from tool call."""
    agent = create_activity_planner_agent(
        grade=params["grade"],
        letter=params["letter"],
        student_level=params["student_level"],
        previously_learned=params.get("previously_learned", []),
        skill_focus=params.get("skill_focus", "isolating_sounds"),
    )

    trigger = HumanMessage(content="Select activities and determine lesson directives for this student.")
    result = await agent.ainvoke({"messages": [trigger]})

    # Extract tool call
    for msg in reversed(result.get("messages", [])):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == PLANNER_TOOL_NAME:
                    return tc.get("args", {})
    return None


def get_git_sha() -> str:
    sha = os.environ.get("GIT_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def generate_report(
    all_results: list[dict],
    duration: float,
    git_sha: str,
) -> str:
    """Generate markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_checks = sum(len(r["checks"]) for r in all_results)
    total_passed = sum(
        sum(1 for c in r["checks"] if c["passed"]) for r in all_results
    )
    overall_score = (total_passed / total_checks * 100) if total_checks else 0

    lines = [
        f"# Planner Directives Eval — {now}",
        f"",
        f"**Git SHA**: `{git_sha}`",
        f"**Duration**: {duration:.1f}s",
        f"**Overall**: {total_passed}/{total_checks} checks passed ({overall_score:.0f}%)",
        f"",
        f"## Results by Fixture",
        f"",
    ]

    for r in all_results:
        fixture_id = r["fixture_id"]
        checks = r["checks"]
        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        score = (passed / total * 100) if total else 0
        status = "PASS" if passed == total else "FAIL"

        lines.append(f"### {fixture_id} — {status} ({passed}/{total}, {score:.0f}%)")
        lines.append(f"")
        lines.append(f"Params: grade={r['grade']}, letter={r['letter']}, level={r['student_level']}")
        lines.append(f"")

        if r.get("error"):
            lines.append(f"**ERROR**: {r['error']}")
            lines.append(f"")
            continue

        lines.append(f"| Field | Expected | Actual | Status |")
        lines.append(f"|-------|----------|--------|--------|")
        for c in checks:
            icon = "pass" if c["passed"] else "**FAIL**"
            exp = str(c["expected"])[:50]
            act = str(c["actual"])[:50]
            lines.append(f"| {c['field']} | {exp} | {act} | {icon} |")

        failures = [c for c in checks if not c["passed"]]
        if failures:
            lines.append(f"")
            lines.append(f"**Failures:**")
            for c in failures:
                lines.append(f"- `{c['field']}`: {c['note']}")

        lines.append(f"")

    # Summary table
    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| Fixture | Score |")
    lines.append(f"|---------|-------|")
    for r in all_results:
        checks = r["checks"]
        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        score = (passed / total * 100) if total else 0
        lines.append(f"| {r['fixture_id']} | {score:.0f}% |")

    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="Run planner directives eval")
    parser.add_argument("--fixture", type=str, help="Run a specific fixture by ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all checks, not just failures")
    args = parser.parse_args()

    fixtures = FIXTURE_PARAMS
    if args.fixture:
        fixtures = [f for f in FIXTURE_PARAMS if f["id"] == args.fixture]
        if not fixtures:
            print(f"Fixture '{args.fixture}' not found. Available: {[f['id'] for f in FIXTURE_PARAMS]}")
            sys.exit(1)

    git_sha = get_git_sha()
    print(f"Planner Directives Eval — {len(fixtures)} fixtures, git {git_sha}")
    print()

    all_results = []
    start = time.time()

    for params in fixtures:
        fixture_id = params["id"]
        print(f"  {fixture_id} ...", end=" ", flush=True)

        result = {
            "fixture_id": fixture_id,
            "grade": params["grade"],
            "letter": params["letter"],
            "student_level": params["student_level"],
            "checks": [],
            "error": None,
        }

        try:
            t0 = time.time()
            plan = await run_planner(params)
            elapsed = time.time() - t0

            if plan is None:
                result["error"] = "Planner did not produce a tool call"
                result["checks"] = [{"field": "tool_call", "expected": "present", "actual": "missing", "passed": False, "note": "no tool call"}]
                print(f"ERROR (no tool call, {elapsed:.1f}s)")
            else:
                checks = validate_directives(plan, params)
                result["checks"] = checks
                passed = sum(1 for c in checks if c["passed"])
                total = len(checks)

                if passed == total:
                    print(f"PASS ({passed}/{total}, {elapsed:.1f}s)")
                else:
                    print(f"FAIL ({passed}/{total}, {elapsed:.1f}s)")
                    for c in checks:
                        if not c["passed"]:
                            print(f"    - {c['field']}: {c['note']}")

        except Exception as e:
            result["error"] = str(e)
            print(f"ERROR: {e}")

        all_results.append(result)

    duration = time.time() - start
    print()

    # Generate report
    report = generate_report(all_results, duration, git_sha)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = os.path.join(RESULTS_DIR, f"planner_directives_{timestamp}.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved: {report_path}")

    # Exit code: 0 if all passed, 1 if any failed
    total_checks = sum(len(r["checks"]) for r in all_results)
    total_passed = sum(sum(1 for c in r["checks"] if c["passed"]) for r in all_results)
    overall = (total_passed / total_checks * 100) if total_checks else 0
    print(f"Overall: {total_passed}/{total_checks} ({overall:.0f}%)")

    sys.exit(0 if total_passed == total_checks else 1)


if __name__ == "__main__":
    asyncio.run(main())
