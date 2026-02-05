"""
Run scaffolding evals (within-section + across-section) on pre-generated fixtures.

Loads lesson fixtures from JSON, runs two LLM judge calls per fixture,
computes scores, and generates a detailed markdown report.

Usage:
    # Run evals on all fixtures
    docker compose exec backend python scripts/run_scaffolding_evals.py

    # Run on specific fixture
    docker compose exec backend python scripts/run_scaffolding_evals.py --fixture k_letter_b_onlevel

    # Use different judge model
    docker compose exec backend python scripts/run_scaffolding_evals.py --model gpt-4o
"""

import argparse
import json
import os
import sys
from datetime import datetime

from app.llm.client import get_chat_model
from tests.evals.models import (
    WithinSectionOutput,
    AcrossSectionOutput,
)


FIXTURES_DIR = "tests/fixtures/handwriting_generator"
RESULTS_DIR = "tests/evals/results"
RUBRICS_DIR = "tests/evals/rubrics"
FORM_D_PATH = "prompt/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/FORM D Scaffolded Activities .md"

DEFAULT_JUDGE_MODEL = "gpt-5.2"


def load_form_d() -> str:
    """Load Form D from the source markdown file."""
    with open(FORM_D_PATH) as f:
        return f.read()


def load_rubric(name: str) -> str:
    """Load a rubric template from the rubrics directory."""
    path = os.path.join(RUBRICS_DIR, f"{name}.md")
    with open(path) as f:
        return f.read()


def load_fixture(fixture_id: str) -> dict:
    """Load a fixture JSON file."""
    path = os.path.join(FIXTURES_DIR, f"{fixture_id}.json")
    with open(path) as f:
        return json.load(f)


def get_available_fixtures() -> list[str]:
    """List available fixture IDs from the fixtures directory."""
    if not os.path.exists(FIXTURES_DIR):
        return []
    return sorted(
        f.replace(".json", "")
        for f in os.listdir(FIXTURES_DIR)
        if f.endswith(".json")
    )


def compute_within_score(output: WithinSectionOutput) -> tuple[int, int, float]:
    """Compute within-section score. Returns (correct, total, percentage)."""
    total_pairs = sum(len(s.pairs) for s in output.sections)
    correct_pairs = sum(
        1 for s in output.sections for p in s.pairs if p.correctly_ordered
    )
    score = (correct_pairs / total_pairs * 100) if total_pairs > 0 else 0.0
    return correct_pairs, total_pairs, score


def compute_across_score(output: AcrossSectionOutput) -> tuple[int, int, float]:
    """Compute across-section score. Returns (correct, total, percentage)."""
    total_links = len(output.links)
    correct_links = sum(1 for link in output.links if link.builds_correctly)
    score = (correct_links / total_links * 100) if total_links > 0 else 0.0
    return correct_links, total_links, score


def run_within_judge(lesson_output: str, model_key: str, form_d: str) -> WithinSectionOutput:
    """Run the within-section scaffolding judge."""
    rubric_template = load_rubric("scaffolding_within_activity")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0)
    judge = model.with_structured_output(WithinSectionOutput)
    return judge.invoke(prompt)


def run_across_judge(lesson_output: str, model_key: str, form_d: str) -> AcrossSectionOutput:
    """Run the across-section scaffolding judge."""
    rubric_template = load_rubric("scaffolding_between_activity")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0)
    judge = model.with_structured_output(AcrossSectionOutput)
    return judge.invoke(prompt)


def format_within_detail(within_output: WithinSectionOutput) -> str:
    """Format within-section detail for the report."""
    lines = []
    for section in within_output.sections:
        lines.append(f"**{section.section_name}**")

        if not section.activities:
            lines.append("_No activities identified_\n")
            continue

        # Activities table
        lines.append("| # | Activity | Difficulty | Reasoning |")
        lines.append("|---|----------|-----------|-----------|")
        for i, act in enumerate(section.activities, 1):
            reasoning = act.reasoning.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {i} | {act.name} | {act.difficulty_level} | {reasoning} |")
        lines.append("")

        # Pairs table
        if section.pairs:
            lines.append("| # | From | To | Ordered? | Reasoning |")
            lines.append("|---|------|----|----------|-----------|")
            for i, pair in enumerate(section.pairs, 1):
                mark = "+" if pair.correctly_ordered else "-"
                reasoning = pair.reasoning.replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {i} | {pair.from_activity} | {pair.to_activity} | {mark} | {reasoning} |"
                )
            lines.append("")
        else:
            lines.append("_No consecutive pairs (0 or 1 activity)_\n")

    lines.append(f"**Judge Summary:** {within_output.explanation}\n")
    return "\n".join(lines)


def format_across_detail(across_output: AcrossSectionOutput) -> str:
    """Format across-section detail for the report."""
    lines = []

    if not across_output.links:
        lines.append("_No cross-section links identified_\n")
    else:
        lines.append("| # | Earlier (Section) | Later (Section) | Builds? | Reasoning |")
        lines.append("|---|-------------------|-----------------|---------|-----------|")
        for i, link in enumerate(across_output.links, 1):
            mark = "+" if link.builds_correctly else "-"
            reasoning = link.reasoning.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {i} | {link.earlier_activity} ({link.earlier_section}) "
                f"| {link.later_activity} ({link.later_section}) | {mark} | {reasoning} |"
            )
        lines.append("")

    lines.append(f"**Judge Summary:** {across_output.explanation}\n")
    return "\n".join(lines)


def generate_report(
    results: list[dict],
    model_key: str,
    run_date: str,
) -> str:
    """Generate the full markdown report."""
    lines = [
        "# Scaffolding Eval Results",
        "",
        f"**Run date:** {run_date}",
        f"**Judge model:** {model_key}",
        f"**Generator model:** gpt-4o",
        f"**Fixtures evaluated:** {len(results)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Fixture | Within | Across | Avg |",
        "|---------|--------|--------|-----|",
    ]

    total_within = 0.0
    total_across = 0.0

    for r in results:
        w = r["within_score"]
        a = r["across_score"]
        avg = (w + a) / 2
        total_within += w
        total_across += a

        lines.append(
            f"| {r['fixture_id']} "
            f"| {w:.1f}% ({r['within_correct']}/{r['within_total']}) "
            f"| {a:.1f}% ({r['across_correct']}/{r['across_total']}) "
            f"| {avg:.1f}% |"
        )

    n = len(results)
    if n > 0:
        avg_within = total_within / n
        avg_across = total_across / n
        avg_overall = (avg_within + avg_across) / 2
        lines.append(
            f"| **Overall Average** | **{avg_within:.1f}%** | **{avg_across:.1f}%** | **{avg_overall:.1f}%** |"
        )

    lines.extend(["", "---", ""])

    # Detailed results per fixture
    lines.append("## Detailed Results\n")

    for r in results:
        fixture = r["fixture"]
        params = fixture["params"]
        lines.append(f"### {r['fixture_id']}")
        lines.append(
            f"**Params:** {params['grade']} | Letter {params['letter']} | {params['student_level']}"
        )
        lines.append("")

        # Within-section detail
        w = r["within_score"]
        lines.append(
            f"#### Within-Section Sequencing: {w:.1f}% ({r['within_correct']}/{r['within_total']} pairs)\n"
        )
        lines.append(r["within_detail"])

        # Across-section detail
        a = r["across_score"]
        lines.append(
            f"#### Across-Section Sequencing: {a:.1f}% ({r['across_correct']}/{r['across_total']} links)\n"
        )
        lines.append(r["across_detail"])

        lines.extend(["---", ""])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run scaffolding evals on pre-generated fixtures")
    parser.add_argument(
        "--fixture", type=str, help="Run on a specific fixture ID only"
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model key (default: {DEFAULT_JUDGE_MODEL})"
    )
    args = parser.parse_args()

    # Determine which fixtures to evaluate
    available = get_available_fixtures()
    if not available:
        print(f"No fixtures found in {FIXTURES_DIR}/")
        print("Run: python scripts/generate_eval_fixtures.py")
        sys.exit(1)

    if args.fixture:
        if args.fixture not in available:
            print(f"Fixture not found: {args.fixture}")
            print(f"Available: {available}")
            sys.exit(1)
        fixture_ids = [args.fixture]
    else:
        fixture_ids = available

    # Load Form D once from source (single source of truth)
    form_d = load_form_d()

    print(f"Running scaffolding evals")
    print(f"  Judge model: {args.model}")
    print(f"  Fixtures: {len(fixture_ids)}")
    print(f"  Form D: loaded from {FORM_D_PATH}")
    print()

    results = []

    for fixture_id in fixture_ids:
        print(f"  Evaluating {fixture_id}...")
        fixture = load_fixture(fixture_id)
        lesson_output = fixture["lesson_output"]

        try:
            # Run both judges
            within_output = run_within_judge(lesson_output, args.model, form_d)
            across_output = run_across_judge(lesson_output, args.model, form_d)

            # Compute scores
            w_correct, w_total, w_score = compute_within_score(within_output)
            a_correct, a_total, a_score = compute_across_score(across_output)

            avg = (w_score + a_score) / 2
            print(
                f"    Within: {w_score:.1f}% ({w_correct}/{w_total}) | "
                f"Across: {a_score:.1f}% ({a_correct}/{a_total}) | "
                f"Avg: {avg:.1f}%"
            )

            results.append({
                "fixture_id": fixture_id,
                "fixture": fixture,
                "within_output": within_output,
                "within_correct": w_correct,
                "within_total": w_total,
                "within_score": w_score,
                "within_detail": format_within_detail(within_output),
                "across_output": across_output,
                "across_correct": a_correct,
                "across_total": a_total,
                "across_score": a_score,
                "across_detail": format_across_detail(across_output),
            })

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    if not results:
        print("\nNo results to report.")
        sys.exit(1)

    # Generate report
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = generate_report(results, args.model, run_date)

    # Save report
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = os.path.join(RESULTS_DIR, f"scaffolding_{timestamp}.md")

    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved: {report_path}")

    # Print summary
    n = len(results)
    avg_within = sum(r["within_score"] for r in results) / n
    avg_across = sum(r["across_score"] for r in results) / n
    avg_overall = (avg_within + avg_across) / 2
    print(f"\nOverall: Within={avg_within:.1f}% | Across={avg_across:.1f}% | Avg={avg_overall:.1f}%")


if __name__ == "__main__":
    main()
