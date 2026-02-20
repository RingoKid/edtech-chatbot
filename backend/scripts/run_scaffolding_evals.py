"""
Run scaffolding evals on pre-generated fixtures.

Loads lesson fixtures from JSON, runs LLM judge calls per fixture,
computes scores, and generates a detailed markdown report.

Usage:
    # Run all 6 evals on all fixtures
    docker compose exec backend python scripts/run_scaffolding_evals.py

    # Run only the two new format evals
    docker compose exec backend python scripts/run_scaffolding_evals.py --eval verbatim structure

    # Run on specific fixture
    docker compose exec backend python scripts/run_scaffolding_evals.py --fixture k_letter_b_onlevel

    # Run on expert fixtures
    docker compose exec backend python scripts/run_scaffolding_evals.py --fixtures-dir tests/fixtures/handwriting_expert

    # Use different judge model
    docker compose exec backend python scripts/run_scaffolding_evals.py --model gpt-4o
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

from app.llm.client import get_chat_model
from tests.evals.models import (
    WithinSectionOutput,
    AcrossSectionOutput,
    GradualReleaseOutput,
    DecompositionOutput,
    VerbatimOutput,
    StructureOutput,
    ThinkAloudOutput,
    CorrectiveFeedbackOutput,
    PostResponseOutput,
    SoundLetterComparisonOutput,
    ScriptSpecificityOutput,
    GradeStandardsOutput,
    ActivityNamingOutput,
    ChildResponseOutput,
)


FIXTURES_DIR = "tests/fixtures/handwriting_generator"
RESULTS_DIR = "tests/evals/results"
RUBRICS_DIR = "tests/evals/rubrics"
FORM_D_PATH = "prompt/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/FORM D Scaffolded Activities .md"
FORM_B_PATH = "prompt/Handwriting & Spelling (Transcription) AI Codes/FORM B-Codes for Lesson Parts Handwriting & Spelling.md"

DEFAULT_JUDGE_MODEL = "gpt-5.2"
JUDGE_TIMEOUT = 120  # seconds per API call before raising an exception
JUDGE_MAX_RETRIES = 2  # retry transient failures (network errors, rate limits)

ALL_EVAL_NAMES = [
    "within", "across", "release", "decomposition", "verbatim", "structure",
    "think_aloud", "corrective_feedback", "post_response", "sound_comparison", "script_specificity",
    "grade_standards", "activity_naming", "child_response_coverage",
]


def get_git_sha() -> str:
    """Get current git commit SHA (short). Checks GIT_SHA env var first (for Docker), falls back to git command."""
    sha = os.environ.get("GIT_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def load_form_d() -> str:
    """Load Form D from the source markdown file."""
    with open(FORM_D_PATH) as f:
        return f.read()


def load_form_b() -> str:
    """Load Form B from the source markdown file."""
    with open(FORM_B_PATH) as f:
        return f.read()


def load_rubric(name: str) -> str:
    """Load a rubric template from the rubrics directory."""
    path = os.path.join(RUBRICS_DIR, f"{name}.md")
    with open(path) as f:
        return f.read()


def load_fixture(fixture_id: str, fixtures_dir: str = FIXTURES_DIR) -> dict:
    """Load a fixture JSON file."""
    path = os.path.join(fixtures_dir, f"{fixture_id}.json")
    with open(path) as f:
        return json.load(f)


def get_available_fixtures(fixtures_dir: str = FIXTURES_DIR) -> list[str]:
    """List available fixture IDs from the fixtures directory."""
    if not os.path.exists(fixtures_dir):
        return []
    return sorted(
        f.replace(".json", "")
        for f in os.listdir(fixtures_dir)
        if f.endswith(".json")
    )


# ---------------------------------------------------------------------------
# Judge functions
# ---------------------------------------------------------------------------

def run_within_judge(lesson_output: str, model_key: str, form_d: str) -> WithinSectionOutput:
    """Run the within-section scaffolding judge."""
    rubric_template = load_rubric("scaffolding_within_activity")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(WithinSectionOutput)
    return judge.invoke(prompt)


def run_across_judge(lesson_output: str, model_key: str, form_d: str) -> AcrossSectionOutput:
    """Run the across-section scaffolding judge."""
    rubric_template = load_rubric("scaffolding_between_activity")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(AcrossSectionOutput)
    return judge.invoke(prompt)


def run_release_judge(lesson_output: str, model_key: str, form_d: str) -> GradualReleaseOutput:
    """Run the gradual release scaffolding judge."""
    rubric_template = load_rubric("scaffolding_gradual_release")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(GradualReleaseOutput)
    return judge.invoke(prompt)


def run_decomposition_judge(lesson_output: str, model_key: str, form_d: str) -> DecompositionOutput:
    """Run the decomposition scaffolding judge."""
    rubric_template = load_rubric("scaffolding_decomposition")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(DecompositionOutput)
    return judge.invoke(prompt)


def run_verbatim_judge(lesson_output: str, model_key: str, form_b: str) -> VerbatimOutput:
    """Run the verbatim explanations judge."""
    rubric_template = load_rubric("verbatim_explanations")
    prompt = rubric_template.replace("{form_b}", form_b).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(VerbatimOutput)
    return judge.invoke(prompt)


def run_structure_judge(lesson_output: str, model_key: str, form_b: str) -> StructureOutput:
    """Run the lesson structure judge."""
    rubric_template = load_rubric("lesson_structure")
    prompt = rubric_template.replace("{form_b}", form_b).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(StructureOutput)
    return judge.invoke(prompt)


def run_think_aloud_judge(lesson_output: str, model_key: str, form_content: None = None) -> ThinkAloudOutput:
    """Run the think-aloud detailed modeling judge."""
    rubric_template = load_rubric("think_aloud")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(ThinkAloudOutput)
    return judge.invoke(prompt)


def run_corrective_feedback_judge(lesson_output: str, model_key: str, form_content: None = None) -> CorrectiveFeedbackOutput:
    """Run the corrective feedback judge."""
    rubric_template = load_rubric("corrective_feedback")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(CorrectiveFeedbackOutput)
    return judge.invoke(prompt)


def run_post_response_judge(lesson_output: str, model_key: str, form_content: None = None) -> PostResponseOutput:
    """Run the post-response explanation judge."""
    rubric_template = load_rubric("post_response_explanation")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(PostResponseOutput)
    return judge.invoke(prompt)


def run_sound_comparison_judge(lesson_output: str, model_key: str, form_content: None = None) -> SoundLetterComparisonOutput:
    """Run the sound/letter comparison judge."""
    rubric_template = load_rubric("sound_letter_comparison")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(SoundLetterComparisonOutput)
    return judge.invoke(prompt)


def run_script_specificity_judge(lesson_output: str, model_key: str, form_content: None = None) -> ScriptSpecificityOutput:
    """Run the script specificity judge."""
    rubric_template = load_rubric("script_specificity")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(ScriptSpecificityOutput)
    return judge.invoke(prompt)


def run_grade_standards_judge(lesson_output: str, model_key: str, form_content: None = None, params: dict = None) -> GradeStandardsOutput:
    """Run the grade-appropriate standards judge."""
    rubric_template = load_rubric("grade_standards")
    grade = params.get("grade", "PreK") if params else "PreK"
    prompt = rubric_template.replace("{grade}", grade).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(GradeStandardsOutput)
    return judge.invoke(prompt)


def run_activity_naming_judge(lesson_output: str, model_key: str, form_d: str) -> ActivityNamingOutput:
    """Run the activity naming judge."""
    rubric_template = load_rubric("activity_naming")
    prompt = rubric_template.replace("{form_d}", form_d).replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(ActivityNamingOutput)
    return judge.invoke(prompt)


def run_child_response_judge(lesson_output: str, model_key: str, form_content: None = None) -> ChildResponseOutput:
    """Run the child response coverage judge."""
    rubric_template = load_rubric("child_response_coverage")
    prompt = rubric_template.replace("{lesson_output}", lesson_output)

    model = get_chat_model(model_key, temperature=0, timeout=JUDGE_TIMEOUT, max_retries=JUDGE_MAX_RETRIES)
    judge = model.with_structured_output(ChildResponseOutput)
    return judge.invoke(prompt)


# ---------------------------------------------------------------------------
# Score computation functions
# ---------------------------------------------------------------------------

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


def compute_release_score(output: GradualReleaseOutput) -> tuple[int, int, float]:
    """Compute gradual release score. Returns (correct, total, percentage)."""
    all_transitions = output.across_section_transitions + output.within_section_transitions
    total = len(all_transitions)
    correct = sum(1 for t in all_transitions if t.support_decreased)
    score = (correct / total * 100) if total > 0 else 0.0
    return correct, total, score


def compute_decomposition_score(output: DecompositionOutput) -> tuple[int, int, float]:
    """Compute decomposition score. Returns (covered, total, percentage)."""
    total_components = sum(len(t.required_components) for t in output.complex_tasks)
    covered = sum(
        1 for t in output.complex_tasks for c in t.required_components if c.is_taught
    )
    score = (covered / total_components * 100) if total_components > 0 else 0.0
    return covered, total_components, score


def compute_verbatim_score(output: VerbatimOutput) -> tuple[int, int, float]:
    """Compute verbatim explanations score. Returns (correct, total, percentage)."""
    total = len(output.sections)
    correct = sum(1 for s in output.sections if s.is_verbatim)
    score = (correct / total * 100) if total > 0 else 0.0
    return correct, total, score


def compute_structure_score(output: StructureOutput) -> tuple[int, int, float]:
    """Compute lesson structure score. Returns (correct, total, percentage)."""
    found_sections = sum(1 for s in output.sections if s.found)
    correct_markers = sum(1 for m in output.markers if m.is_correct)
    total = len(output.sections) + len(output.markers)
    correct = found_sections + correct_markers
    score = (correct / total * 100) if total > 0 else 0.0
    return correct, total, score


def compute_think_aloud_score(output: ThinkAloudOutput) -> tuple[int, int, float]:
    """Compute think-aloud score. Returns (correct, total, percentage).

    Per instance: count True among 5 checklist items. If worked_example_present
    is False, the other 4 are automatically False. Average across instances.
    """
    if not output.instances:
        return 0, 5, 0.0

    total_true = 0
    total_items = 0
    for inst in output.instances:
        if not inst.worked_example_present:
            # No example → all 5 items are False
            total_items += 5
        else:
            items = [
                inst.worked_example_present,
                inst.uses_specific_word,
                inst.narrates_reasoning,
                inst.shows_steps_sequentially,
                inst.connects_sound_to_letter,
            ]
            total_true += sum(items)
            total_items += 5

    score = (total_true / total_items * 100) if total_items > 0 else 0.0
    return total_true, total_items, score


def compute_corrective_feedback_score(output: CorrectiveFeedbackOutput) -> tuple[int, int, float]:
    """Compute corrective feedback score. Returns (correct, total, percentage).

    If no blocks found: 0/4. Otherwise: best block's True count / 4.
    """
    if not output.blocks:
        return 0, 4, 0.0

    best_count = 0
    for block in output.blocks:
        count = sum([
            block.is_plausible,
            block.has_scripted_response,
            block.explains_difference,
            block.engages_students,
        ])
        best_count = max(best_count, count)

    score = (best_count / 4 * 100)
    return best_count, 4, score


def compute_post_response_score(output: PostResponseOutput) -> tuple[int, int, float]:
    """Compute post-response explanation score. Returns (correct, total, percentage).

    Count responses with followed_by == "explanation" / total responses.
    Uses a minimum response floor of 3 to prevent sparse lessons from scoring
    artificially high (e.g., 1/1 = 100%).
    """
    MIN_RESPONSE_FLOOR = 3

    all_responses = [
        resp
        for act in output.activities
        for resp in act.first_two_responses
    ]
    found = len(all_responses)
    if found == 0:
        return 0, MIN_RESPONSE_FLOOR, 0.0

    explanations = sum(1 for r in all_responses if r.followed_by == "explanation")
    denominator = max(found, MIN_RESPONSE_FLOOR)
    score = (explanations / denominator * 100)
    return explanations, denominator, score


def compute_sound_comparison_score(output: SoundLetterComparisonOutput) -> tuple[int, int, float]:
    """Compute sound/letter comparison score. Returns (correct, total, percentage).

    If no comparisons found: 0/4. Otherwise: best block's True count / 4.
    """
    if not output.comparisons:
        return 0, 4, 0.0

    best_count = 0
    for comp in output.comparisons:
        count = sum([
            comp.describes_similarity,
            comp.describes_difference,
            comp.includes_articulatory_detail,
            comp.students_produce_both,
        ])
        best_count = max(best_count, count)

    score = (best_count / 4 * 100)
    return best_count, 4, score


def compute_script_specificity_score(output: ScriptSpecificityOutput) -> tuple[int, int, float]:
    """Compute script specificity composite score. Returns (correct, total, percentage).

    Composite = volume_adjusted_dialogue × 0.5 + response_specificity × 0.3 + pacing_score × 0.2

    The dialogue sub-metric uses per-section volume scaling: each section's dialogue
    ratio is multiplied by min(1.0, dialogue_lines / VOLUME_FLOOR) to penalize sections
    with very few scripted lines. This prevents a lesson with 2 dialogue lines and
    0 directions from scoring the same as one with 30 dialogue lines and 5 directions.
    """
    VOLUME_FLOOR = 10  # minimum expected dialogue lines per section

    total_specific_resp = sum(s.specific_child_responses for s in output.sections)
    total_generic_resp = sum(s.generic_child_responses for s in output.sections)
    pacing_sections = sum(1 for s in output.sections if s.has_pacing_cues)

    # Per-section volume-adjusted dialogue ratio
    section_scores = []
    for s in output.sections:
        section_total = s.dialogue_lines + s.stage_directions
        ratio = (s.dialogue_lines / section_total) if section_total > 0 else 0.0
        volume_scale = min(1.0, s.dialogue_lines / VOLUME_FLOOR)
        section_scores.append(ratio * volume_scale)

    num_sections = len(output.sections) if output.sections else 4
    dialogue_score = (sum(section_scores) / num_sections) if num_sections > 0 else 0.0

    resp_denom = total_specific_resp + total_generic_resp
    response_specificity = (total_specific_resp / resp_denom) if resp_denom > 0 else 0.0

    pacing_score = pacing_sections / num_sections

    composite = (dialogue_score * 0.5) + (response_specificity * 0.3) + (pacing_score * 0.2)
    score = composite * 100

    # Use composite percentage as correct out of 100
    return round(score, 1), 100, score


def compute_grade_standards_score(output: GradeStandardsOutput) -> tuple[int, int, float]:
    """Compute grade standards composite score. Returns (correct, total, percentage).

    Composite = standards_accuracy × 0.5 + developmental_appropriateness × 0.5
    """
    # Standards accuracy: all three bools must be True
    total_standards = len(output.standards)
    if total_standards > 0:
        correct_standards = sum(
            1 for s in output.standards
            if s.correct_system and s.valid_code and s.relevant_to_handwriting
        )
        standards_accuracy = correct_standards / total_standards
    else:
        correct_standards = 0
        standards_accuracy = 0.0

    # Developmental appropriateness
    total_dev = len(output.developmental_checks)
    if total_dev > 0:
        appropriate_dev = sum(1 for d in output.developmental_checks if d.appropriate)
        dev_score = appropriate_dev / total_dev
    else:
        appropriate_dev = 0
        dev_score = 0.0

    composite = (standards_accuracy * 0.5 + dev_score * 0.5) * 100

    # For the summary row, report composite as "correct" out of 100
    return round(composite, 1), 100, composite


def _activity_name_match(name: str, candidates: list[str]) -> bool:
    """Check if an activity name matches any candidate using normalized substring matching."""
    name_lower = name.lower().strip()
    for candidate in candidates:
        c_lower = candidate.lower().strip()
        if name_lower == c_lower or name_lower in c_lower or c_lower in name_lower:
            return True
    return False


def compute_activity_naming_score(output: ActivityNamingOutput) -> tuple[int, int, float]:
    """Compute activity naming composite score. Returns (correct, total, percentage).

    Composite = section_naming × 0.6 + materials_coverage × 0.4
    """
    # Section naming: sections with has_named_activity / 4
    named_sections = sum(1 for s in output.sections if s.has_named_activity)
    section_score = named_sections / 4 if output.sections else 0.0

    # Materials coverage: activities in lesson that appear in materials / total in lesson
    activities_in_lesson = output.materials_check.activities_in_lesson
    activities_listed = output.materials_check.activities_listed
    if activities_in_lesson:
        covered = sum(1 for a in activities_in_lesson if _activity_name_match(a, activities_listed))
        materials_score = covered / len(activities_in_lesson)
    else:
        covered = 0
        materials_score = 0.0

    composite = (section_score * 0.6 + materials_score * 0.4) * 100

    return round(composite, 1), 100, composite


def compute_child_response_score(output: ChildResponseOutput) -> tuple[int, int, float]:
    """Compute child response coverage composite score. Returns (correct, total, percentage).

    Composite = presence × 0.3 + specificity × 0.3 + completeness × 0.4
    """
    interactions = output.interactions
    total = len(interactions)

    if total == 0:
        return 0, 0, 0.0

    # Presence
    with_response = sum(1 for i in interactions if i.has_response)
    presence = with_response / total

    # Specificity (of those that have a response)
    if with_response > 0:
        specific = sum(1 for i in interactions if i.has_response and i.is_specific)
        specificity = specific / with_response
    else:
        specificity = 0.0

    # Component completeness
    complete = 0
    for i in interactions:
        verbal_ok = (not i.needs_verbal) or i.has_verbal_component
        action_ok = (not i.needs_action) or i.has_action_component
        if verbal_ok and action_ok:
            complete += 1
    completeness = complete / total

    composite = (presence * 0.3 + specificity * 0.3 + completeness * 0.4) * 100

    return round(composite, 1), 100, composite


# ---------------------------------------------------------------------------
# Format functions
# ---------------------------------------------------------------------------

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


def format_release_detail(output: GradualReleaseOutput) -> str:
    """Format gradual release output as markdown tables."""
    lines = []

    # Across-section support levels
    lines.append("**Across-Section Support Levels**")
    lines.append("| Section | Support Level | Indicators |")
    lines.append("|---------|-------------|------------|")
    for level in output.across_section_levels:
        indicators = "; ".join(
            ind.replace("|", "\\|").replace("\n", " ") for ind in level.indicators
        )
        lines.append(f"| {level.section_or_step} | {level.support_level} | {indicators} |")
    lines.append("")

    # Across-section transitions
    lines.append("**Across-Section Transitions**")
    lines.append("| # | From | To | Released? | Reasoning |")
    lines.append("|---|------|----|----------|-----------|")
    for i, t in enumerate(output.across_section_transitions, 1):
        mark = "+" if t.support_decreased else "-"
        reasoning = t.reasoning.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | {t.from_step} | {t.to_step} | {mark} | {reasoning} |")
    lines.append("")

    # Within Section 3 levels
    lines.append("**Within Section 3 (Guided Practice)**")
    if output.within_section_levels:
        lines.append("| # | Step | Support Level | Indicators |")
        lines.append("|---|------|-------------|------------|")
        for i, level in enumerate(output.within_section_levels, 1):
            indicators = "; ".join(
                ind.replace("|", "\\|").replace("\n", " ") for ind in level.indicators
            )
            lines.append(f"| {i} | {level.section_or_step} | {level.support_level} | {indicators} |")
        lines.append("")

    # Within Section 3 transitions
    if output.within_section_transitions:
        lines.append("| # | From | To | Released? | Reasoning |")
        lines.append("|---|------|----|----------|-----------|")
        for i, t in enumerate(output.within_section_transitions, 1):
            mark = "+" if t.support_decreased else "-"
            reasoning = t.reasoning.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {i} | {t.from_step} | {t.to_step} | {mark} | {reasoning} |")
        lines.append("")
    else:
        lines.append("_No within-section transitions (0 or 1 step)_\n")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_decomposition_detail(output: DecompositionOutput) -> str:
    """Format decomposition output as markdown tables."""
    lines = []

    if not output.complex_tasks:
        lines.append("_No complex tasks identified_\n")
    else:
        lines.append("| Complex Task (Section) | Component Skill | Taught? | Where | Reasoning |")
        lines.append("|------------------------|----------------|---------|-------|-----------| ")
        for task in output.complex_tasks:
            for comp in task.required_components:
                mark = "+" if comp.is_taught else "-"
                where = (
                    f"{comp.taught_via_activity} ({comp.taught_in_section})"
                    if comp.is_taught and comp.taught_in_section
                    else "—"
                )
                reasoning = comp.reasoning.replace("|", "\\|").replace("\n", " ")
                task_label = f"{task.task_name} ({task.section})"
                task_label = task_label.replace("|", "\\|")
                lines.append(f"| {task_label} | {comp.skill_name} | {mark} | {where} | {reasoning} |")
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_verbatim_detail(output: VerbatimOutput) -> str:
    """Format verbatim explanations output as a markdown table."""
    lines = []

    lines.append("| # | Section | Found? | Verbatim? | Differences | Reasoning |")
    lines.append("|---|---------|--------|-----------|-------------|-----------|")
    for i, section in enumerate(output.sections, 1):
        found_mark = "+" if section.found else "-"
        verbatim_mark = "+" if section.is_verbatim else "-"
        differences = section.differences.replace("|", "\\|").replace("\n", " ") if section.differences else "—"
        reasoning = section.reasoning.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {i} | {section.section_name} | {found_mark} | {verbatim_mark} "
            f"| {differences} | {reasoning} |"
        )
    lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_structure_detail(output: StructureOutput) -> str:
    """Format lesson structure output as two markdown tables."""
    lines = []

    # Sections table
    found_count = sum(1 for s in output.sections if s.found)
    lines.append(f"**Sections ({found_count}/{len(output.sections)})**")
    lines.append("| # | Expected | Found? | Actual Heading | Reasoning |")
    lines.append("|---|----------|--------|----------------|-----------|")
    for i, section in enumerate(output.sections, 1):
        mark = "+" if section.found else "-"
        actual = section.actual_heading if section.actual_heading else "—"
        actual = actual.replace("|", "\\|").replace("\n", " ")
        reasoning = section.reasoning.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | {section.expected_name} | {mark} | {actual} | {reasoning} |")
    lines.append("")

    # Markers table
    correct_count = sum(1 for m in output.markers if m.is_correct)
    lines.append(f"**Markers ({correct_count}/{len(output.markers)})**")
    lines.append("| # | Marker | Symbol | Correct? | Consistency | Issues | Reasoning |")
    lines.append("|---|--------|--------|----------|-------------|--------|-----------|")
    for i, marker in enumerate(output.markers, 1):
        mark = "+" if marker.is_correct else "-"
        consistency = marker.consistency_note.replace("|", "\\|").replace("\n", " ")
        issues = marker.issues.replace("|", "\\|").replace("\n", " ") if marker.issues else "—"
        reasoning = marker.reasoning.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {i} | {marker.marker_name} | {marker.marker_symbol} | {mark} "
            f"| {consistency} | {issues} | {reasoning} |"
        )
    lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_think_aloud_detail(output: ThinkAloudOutput) -> str:
    """Format think-aloud output as a markdown table."""
    lines = []

    if not output.instances:
        lines.append("_No sections with independent student work identified_\n")
    else:
        lines.append("| Section | Task | Example? | Specific Word? | Narrates? | Steps? | Sound→Letter? | Evidence |")
        lines.append("|---------|------|----------|----------------|-----------|--------|---------------|----------|")
        for inst in output.instances:
            evidence = inst.evidence.replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(
                f"| {inst.section} | {inst.task_description.replace('|', '\\|')} "
                f"| {'+'if inst.worked_example_present else '-'} "
                f"| {'+'if inst.uses_specific_word else '-'} "
                f"| {'+'if inst.narrates_reasoning else '-'} "
                f"| {'+'if inst.shows_steps_sequentially else '-'} "
                f"| {'+'if inst.connects_sound_to_letter else '-'} "
                f'| "{evidence}" |'
            )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_corrective_feedback_detail(output: CorrectiveFeedbackOutput) -> str:
    """Format corrective feedback output as a markdown table."""
    lines = []

    if not output.blocks:
        lines.append("_No corrective feedback blocks found_\n")
    else:
        lines.append("| Location | Error Anticipated | Plausible? | Scripted? | Explains? | Engages? | Evidence |")
        lines.append("|----------|-------------------|------------|-----------|-----------|----------|----------|")
        for block in output.blocks:
            evidence = block.evidence.replace("|", "\\|").replace("\n", " ")[:120]
            error = block.anticipated_error.replace("|", "\\|")
            lines.append(
                f"| {block.location} | {error} "
                f"| {'+'if block.is_plausible else '-'} "
                f"| {'+'if block.has_scripted_response else '-'} "
                f"| {'+'if block.explains_difference else '-'} "
                f"| {'+'if block.engages_students else '-'} "
                f'| "{evidence}" |'
            )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_post_response_detail(output: PostResponseOutput) -> str:
    """Format post-response explanation output as a markdown table."""
    lines = []

    if not output.activities:
        lines.append("_No activities with student responses identified_\n")
    else:
        lines.append("| Section | Activity | Response | Followed By | Teacher Text |")
        lines.append("|---------|----------|----------|-------------|--------------|")
        for act in output.activities:
            for resp in act.first_two_responses:
                response_text = resp.response_text.replace("|", "\\|").replace("\n", " ")
                teacher_text = resp.teacher_text.replace("|", "\\|").replace("\n", " ")[:120]
                lines.append(
                    f"| {act.section} | {act.activity_name.replace('|', '\\|')} "
                    f"| {response_text} | {resp.followed_by} "
                    f'| "{teacher_text}" |'
                )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_sound_comparison_detail(output: SoundLetterComparisonOutput) -> str:
    """Format sound/letter comparison output as a markdown table."""
    lines = []

    if not output.comparisons:
        lines.append("_No sound/letter comparisons found_\n")
    else:
        lines.append("| Location | Target | Compared With | Similarity? | Difference? | Articulatory? | Students Produce? | Evidence |")
        lines.append("|----------|--------|---------------|-------------|-------------|---------------|-------------------|----------|")
        for comp in output.comparisons:
            evidence = comp.evidence.replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(
                f"| {comp.location} | {comp.target} | {comp.compared_with} "
                f"| {'+'if comp.describes_similarity else '-'} "
                f"| {'+'if comp.describes_difference else '-'} "
                f"| {'+'if comp.includes_articulatory_detail else '-'} "
                f"| {'+'if comp.students_produce_both else '-'} "
                f'| "{evidence}" |'
            )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_script_specificity_detail(output: ScriptSpecificityOutput) -> str:
    """Format script specificity output as a markdown table with sub-metrics."""
    lines = []

    if not output.sections:
        lines.append("_No sections analyzed_\n")
    else:
        lines.append("| Section | Dialogue | Directions | Examples | Specific Resp. | Generic Resp. | Pacing? |")
        lines.append("|---------|----------|------------|----------|----------------|---------------|---------|")

        total_dialogue = 0
        total_directions = 0
        total_examples = 0
        all_example_words = []
        total_specific = 0
        total_generic = 0
        pacing_count = 0

        for s in output.sections:
            example_list = ", ".join(s.specific_example_words) if s.specific_example_words else "—"
            example_list = example_list.replace("|", "\\|")
            word_count = len(s.specific_example_words)
            lines.append(
                f"| {s.section} | {s.dialogue_lines} | {s.stage_directions} "
                f"| {word_count} ({example_list}) | {s.specific_child_responses} "
                f"| {s.generic_child_responses} | {'+'if s.has_pacing_cues else '-'} |"
            )
            total_dialogue += s.dialogue_lines
            total_directions += s.stage_directions
            total_examples += word_count
            all_example_words.extend(s.specific_example_words)
            total_specific += s.specific_child_responses
            total_generic += s.generic_child_responses
            if s.has_pacing_cues:
                pacing_count += 1

        num_sections = len(output.sections)
        lines.append(
            f"| **Totals** | **{total_dialogue}** | **{total_directions}** "
            f"| **{total_examples} words** | **{total_specific}** "
            f"| **{total_generic}** | **{pacing_count}/{num_sections}** |"
        )
        lines.append("")

        # Sub-metrics (volume-adjusted dialogue matches compute function)
        VOLUME_FLOOR = 10
        section_scores = []
        for s in output.sections:
            sec_total = s.dialogue_lines + s.stage_directions
            ratio = (s.dialogue_lines / sec_total) if sec_total > 0 else 0.0
            vol_scale = min(1.0, s.dialogue_lines / VOLUME_FLOOR)
            section_scores.append(ratio * vol_scale)
        dialogue_adj = (sum(section_scores) / num_sections * 100) if num_sections > 0 else 0.0

        resp_denom = total_specific + total_generic
        resp_ratio = (total_specific / resp_denom * 100) if resp_denom > 0 else 0.0
        pacing_pct = (pacing_count / num_sections * 100) if num_sections > 0 else 0.0

        lines.append(
            f"Sub-metrics: Dialogue (vol-adj): {dialogue_adj:.1f}% | Examples: {total_examples} words "
            f"| Responses: {resp_ratio:.1f}% | Pacing: {pacing_pct:.1f}%"
        )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_grade_standards_detail(output: GradeStandardsOutput) -> str:
    """Format grade standards output as markdown tables."""
    lines = []

    # Standards table
    total_standards = len(output.standards)
    correct_standards = sum(
        1 for s in output.standards
        if s.correct_system and s.valid_code and s.relevant_to_handwriting
    )
    lines.append(f"**Standards ({correct_standards}/{total_standards})**")

    if not output.standards:
        lines.append("_No standards found in lesson_\n")
    else:
        lines.append("| Code | System? | Valid? | Relevant? | Reasoning |")
        lines.append("|------|---------|--------|-----------|-----------|")
        for s in output.standards:
            reasoning = s.reasoning.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {s.code} "
                f"| {'+'if s.correct_system else '-'} "
                f"| {'+'if s.valid_code else '-'} "
                f"| {'+'if s.relevant_to_handwriting else '-'} "
                f"| {reasoning} |"
            )
        lines.append("")

    # Developmental checks table
    total_dev = len(output.developmental_checks)
    appropriate_dev = sum(1 for d in output.developmental_checks if d.appropriate)
    lines.append(f"**Developmental Appropriateness ({appropriate_dev}/{total_dev})**")

    if not output.developmental_checks:
        lines.append("_No developmental checks performed_\n")
    else:
        lines.append("| Criterion | Appropriate? | Evidence | Reasoning |")
        lines.append("|-----------|-------------|----------|-----------|")
        for d in output.developmental_checks:
            evidence = d.evidence.replace("|", "\\|").replace("\n", " ")[:120]
            reasoning = d.reasoning.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {d.criterion} "
                f"| {'+'if d.appropriate else '-'} "
                f'| "{evidence}" '
                f"| {reasoning} |"
            )
        lines.append("")

    # Sub-scores
    std_pct = (correct_standards / total_standards * 100) if total_standards > 0 else 0.0
    dev_pct = (appropriate_dev / total_dev * 100) if total_dev > 0 else 0.0
    lines.append(
        f"Sub-metrics: Standards: {std_pct:.1f}% {correct_standards}/{total_standards} "
        f"| Dev: {dev_pct:.1f}% {appropriate_dev}/{total_dev}"
    )
    lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_activity_naming_detail(output: ActivityNamingOutput) -> str:
    """Format activity naming output as markdown tables."""
    lines = []

    # Section activity coverage table
    named_count = sum(1 for s in output.sections if s.has_named_activity)
    lines.append(f"**Section Activity Coverage ({named_count}/{len(output.sections)})**")

    if not output.sections:
        lines.append("_No sections analyzed_\n")
    else:
        lines.append("| Section | Named? | Named Activities | Generic Descriptions | Evidence |")
        lines.append("|---------|--------|-----------------|---------------------|----------|")
        for s in output.sections:
            named = ", ".join(s.named_activities) if s.named_activities else "—"
            named = named.replace("|", "\\|")
            generic = "; ".join(s.generic_descriptions) if s.generic_descriptions else "—"
            generic = generic.replace("|", "\\|").replace("\n", " ")[:120]
            evidence = s.evidence.replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(
                f"| {s.section} "
                f"| {'+'if s.has_named_activity else '-'} "
                f"| {named} "
                f"| {generic} "
                f'| "{evidence}" |'
            )
        lines.append("")

    # Materials coverage table
    mc = output.materials_check
    activities_in_lesson = mc.activities_in_lesson
    activities_listed = mc.activities_listed
    if activities_in_lesson:
        covered = sum(1 for a in activities_in_lesson if _activity_name_match(a, activities_listed))
    else:
        covered = 0

    lines.append(f"**Materials Coverage ({covered}/{len(activities_in_lesson)})**")
    if activities_in_lesson:
        lines.append("| Activity | In Materials? |")
        lines.append("|----------|--------------|")
        for a in activities_in_lesson:
            in_mat = "+" if _activity_name_match(a, activities_listed) else "-"
            lines.append(f"| {a} | {in_mat} |")
        lines.append("")
    else:
        lines.append("_No named activities found in lesson_\n")

    if mc.missing_from_materials:
        lines.append(f"Missing from Materials: {', '.join(mc.missing_from_materials)}")
        lines.append("")

    # Sub-scores
    section_pct = (named_count / 4 * 100) if output.sections else 0.0
    mat_pct = (covered / len(activities_in_lesson) * 100) if activities_in_lesson else 0.0
    lines.append(
        f"Sub-metrics: Sections: {section_pct:.1f}% {named_count}/4 "
        f"| Materials: {mat_pct:.1f}% {covered}/{len(activities_in_lesson)}"
    )
    lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


def format_child_response_detail(output: ChildResponseOutput) -> str:
    """Format child response coverage output as a markdown table."""
    lines = []

    interactions = output.interactions
    total = len(interactions)

    if not interactions:
        lines.append("_No interaction points identified_\n")
    else:
        lines.append("| Section | Teacher Prompt | Type | Response? | Specific? | Verbal? | Action? | Needs V? | Needs A? | Response Text |")
        lines.append("|---------|---------------|------|-----------|-----------|---------|---------|----------|----------|---------------|")
        for i in interactions:
            prompt = i.teacher_prompt.replace("|", "\\|").replace("\n", " ")[:60]
            resp = i.response_text.replace("|", "\\|").replace("\n", " ")[:80]
            lines.append(
                f"| {i.section} "
                f"| {prompt} "
                f"| {i.prompt_type} "
                f"| {'+'if i.has_response else '-'} "
                f"| {'+'if i.is_specific else '-'} "
                f"| {'+'if i.has_verbal_component else '-'} "
                f"| {'+'if i.has_action_component else '-'} "
                f"| {'+'if i.needs_verbal else '-'} "
                f"| {'+'if i.needs_action else '-'} "
                f'| "{resp}" |'
            )
        lines.append("")

    # Sub-scores
    if total > 0:
        with_response = sum(1 for i in interactions if i.has_response)
        presence_pct = with_response / total * 100
        if with_response > 0:
            specific = sum(1 for i in interactions if i.has_response and i.is_specific)
            specificity_pct = specific / with_response * 100
        else:
            specific = 0
            specificity_pct = 0.0

        complete = 0
        for i in interactions:
            verbal_ok = (not i.needs_verbal) or i.has_verbal_component
            action_ok = (not i.needs_action) or i.has_action_component
            if verbal_ok and action_ok:
                complete += 1
        completeness_pct = complete / total * 100

        lines.append(
            f"Sub-metrics: Present: {presence_pct:.1f}% {with_response}/{total} "
            f"| Specific: {specificity_pct:.1f}% {specific}/{with_response} "
            f"| Complete: {completeness_pct:.1f}% {complete}/{total}"
        )
        lines.append("")

    lines.append(f"**Judge Summary:** {output.explanation}\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Eval registry — maps eval name to its functions and form dependency
# ---------------------------------------------------------------------------

EVAL_REGISTRY = {
    "within": {
        "label": "Within",
        "unit": "pairs",
        "form": "form_d",
        "judge_fn": run_within_judge,
        "compute_fn": compute_within_score,
        "format_fn": format_within_detail,
    },
    "across": {
        "label": "Across",
        "unit": "links",
        "form": "form_d",
        "judge_fn": run_across_judge,
        "compute_fn": compute_across_score,
        "format_fn": format_across_detail,
    },
    "release": {
        "label": "Release",
        "unit": "transitions",
        "form": "form_d",
        "judge_fn": run_release_judge,
        "compute_fn": compute_release_score,
        "format_fn": format_release_detail,
    },
    "decomposition": {
        "label": "Decomp",
        "unit": "components",
        "form": "form_d",
        "judge_fn": run_decomposition_judge,
        "compute_fn": compute_decomposition_score,
        "format_fn": format_decomposition_detail,
    },
    "verbatim": {
        "label": "Verbatim",
        "unit": "sections",
        "form": "form_b",
        "judge_fn": run_verbatim_judge,
        "compute_fn": compute_verbatim_score,
        "format_fn": format_verbatim_detail,
    },
    "structure": {
        "label": "Structure",
        "unit": "checks",
        "form": "form_b",
        "judge_fn": run_structure_judge,
        "compute_fn": compute_structure_score,
        "format_fn": format_structure_detail,
    },
    "think_aloud": {
        "label": "ThinkAloud",
        "unit": "items",
        "form": "none",
        "judge_fn": run_think_aloud_judge,
        "compute_fn": compute_think_aloud_score,
        "format_fn": format_think_aloud_detail,
    },
    "corrective_feedback": {
        "label": "Corrective",
        "unit": "items",
        "form": "none",
        "judge_fn": run_corrective_feedback_judge,
        "compute_fn": compute_corrective_feedback_score,
        "format_fn": format_corrective_feedback_detail,
    },
    "post_response": {
        "label": "PostResp",
        "unit": "responses",
        "form": "none",
        "judge_fn": run_post_response_judge,
        "compute_fn": compute_post_response_score,
        "format_fn": format_post_response_detail,
    },
    "sound_comparison": {
        "label": "SoundComp",
        "unit": "items",
        "form": "none",
        "judge_fn": run_sound_comparison_judge,
        "compute_fn": compute_sound_comparison_score,
        "format_fn": format_sound_comparison_detail,
    },
    "script_specificity": {
        "label": "Specificity",
        "unit": "composite",
        "form": "none",
        "judge_fn": run_script_specificity_judge,
        "compute_fn": compute_script_specificity_score,
        "format_fn": format_script_specificity_detail,
    },
    "grade_standards": {
        "label": "GradeStd",
        "unit": "composite",
        "form": "none",
        "uses_params": True,
        "judge_fn": run_grade_standards_judge,
        "compute_fn": compute_grade_standards_score,
        "format_fn": format_grade_standards_detail,
    },
    "activity_naming": {
        "label": "ActName",
        "unit": "composite",
        "form": "form_d",
        "judge_fn": run_activity_naming_judge,
        "compute_fn": compute_activity_naming_score,
        "format_fn": format_activity_naming_detail,
    },
    "child_response_coverage": {
        "label": "ChildResp",
        "unit": "composite",
        "form": "none",
        "judge_fn": run_child_response_judge,
        "compute_fn": compute_child_response_score,
        "format_fn": format_child_response_detail,
    },
}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    results: list[dict],
    eval_names: list[str],
    model_key: str,
    run_date: str,
    git_sha: str,
    fixtures_dir: str = FIXTURES_DIR,
) -> str:
    """Generate the full markdown report. Only includes columns for evals that ran."""
    lines = [
        "# Scaffolding Eval Results",
        "",
        f"**Run date:** {run_date}",
        f"**Git SHA:** {git_sha}",
        f"**Judge model:** {model_key}",
        f"**Evals:** {', '.join(eval_names)}",
        f"**Fixtures dir:** {os.path.basename(os.path.normpath(fixtures_dir))}",
        f"**Fixtures evaluated:** {len(results)}",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    # Build dynamic summary table header
    labels = [EVAL_REGISTRY[name]["label"] for name in eval_names]
    header = "| Fixture | " + " | ".join(labels) + " | Avg |"
    separator = "|---------|" + "|".join("-----" for _ in labels) + "|-----|"
    lines.append(header)
    lines.append(separator)

    # Accumulate totals per eval
    totals = {name: 0.0 for name in eval_names}

    for r in results:
        scores = []
        cells = []
        for name in eval_names:
            s = r[f"{name}_score"]
            c = r[f"{name}_correct"]
            t = r[f"{name}_total"]
            scores.append(s)
            totals[name] += s
            cells.append(f"{s:.1f}% ({c}/{t})")

        avg = sum(scores) / len(scores)
        line = f"| {r['fixture_id']} | " + " | ".join(cells) + f" | {avg:.1f}% |"
        lines.append(line)

    n = len(results)
    if n > 0:
        avg_cells = []
        avg_scores = []
        for name in eval_names:
            avg_val = totals[name] / n
            avg_scores.append(avg_val)
            avg_cells.append(f"**{avg_val:.1f}%**")
        avg_overall = sum(avg_scores) / len(avg_scores)
        line = "| **Overall Average** | " + " | ".join(avg_cells) + f" | **{avg_overall:.1f}%** |"
        lines.append(line)

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

        for name in eval_names:
            entry = EVAL_REGISTRY[name]
            s = r[f"{name}_score"]
            c = r[f"{name}_correct"]
            t = r[f"{name}_total"]
            lines.append(
                f"#### {entry['label']}: {s:.1f}% ({c}/{t} {entry['unit']})\n"
            )
            lines.append(r[f"{name}_detail"])

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
    parser.add_argument(
        "--fixtures-dir", type=str, default=FIXTURES_DIR,
        help=f"Directory containing fixture JSON files (default: {FIXTURES_DIR})"
    )
    parser.add_argument(
        "--eval", nargs="+", choices=ALL_EVAL_NAMES, dest="evals",
        help="Which evals to run (default: all). Valid: " + ", ".join(ALL_EVAL_NAMES)
    )
    args = parser.parse_args()

    fixtures_dir = args.fixtures_dir
    eval_names = args.evals if args.evals else ALL_EVAL_NAMES

    # Determine which fixtures to evaluate
    available = get_available_fixtures(fixtures_dir)
    if not available:
        print(f"No fixtures found in {fixtures_dir}/")
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

    # Load forms only when needed
    needed_forms = set(EVAL_REGISTRY[name]["form"] for name in eval_names)
    forms = {}
    if "form_d" in needed_forms:
        forms["form_d"] = load_form_d()
        print(f"  Form D: loaded from {FORM_D_PATH}")
    if "form_b" in needed_forms:
        forms["form_b"] = load_form_b()
        print(f"  Form B: loaded from {FORM_B_PATH}")
    if "none" in needed_forms:
        forms["none"] = None  # Self-contained rubrics, no form needed

    print(f"Running scaffolding evals")
    print(f"  Judge model: {args.model}")
    print(f"  Evals: {', '.join(eval_names)}")
    print(f"  Fixtures dir: {fixtures_dir}")
    print(f"  Fixtures: {len(fixture_ids)}")
    print()

    results = []

    for fixture_id in fixture_ids:
        print(f"  Evaluating {fixture_id}...")
        fixture = load_fixture(fixture_id, fixtures_dir)
        lesson_output = fixture["lesson_output"]

        try:
            result = {"fixture_id": fixture_id, "fixture": fixture}
            scores = []

            for name in eval_names:
                entry = EVAL_REGISTRY[name]
                form_content = forms[entry["form"]]

                # Run judge — pass params when eval needs them (e.g., grade_standards)
                if entry.get("uses_params"):
                    judge_output = entry["judge_fn"](lesson_output, args.model, form_content, params=fixture.get("params", {}))
                else:
                    judge_output = entry["judge_fn"](lesson_output, args.model, form_content)

                # Compute score
                correct, total, score = entry["compute_fn"](judge_output)

                # Format detail
                detail = entry["format_fn"](judge_output)

                result[f"{name}_output"] = judge_output
                result[f"{name}_correct"] = correct
                result[f"{name}_total"] = total
                result[f"{name}_score"] = score
                result[f"{name}_detail"] = detail
                scores.append(score)

            avg = sum(scores) / len(scores)
            # Console output
            parts = []
            for name in eval_names:
                label = EVAL_REGISTRY[name]["label"]
                s = result[f"{name}_score"]
                c = result[f"{name}_correct"]
                t = result[f"{name}_total"]
                parts.append(f"{label}: {s:.1f}% ({c}/{t})")
            parts.append(f"Avg: {avg:.1f}%")
            print(f"    {' | '.join(parts)}")

            results.append(result)

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    if not results:
        print("\nNo results to report.")
        sys.exit(1)

    # Generate report
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_sha = get_git_sha()
    report = generate_report(results, eval_names, args.model, run_date, git_sha, fixtures_dir)

    # Save report
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = os.path.join(RESULTS_DIR, f"scaffolding_{timestamp}.md")

    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved: {report_path}")

    # Print summary
    n = len(results)
    parts = []
    avg_scores = []
    for name in eval_names:
        avg_val = sum(r[f"{name}_score"] for r in results) / n
        avg_scores.append(avg_val)
        label = EVAL_REGISTRY[name]["label"]
        parts.append(f"{label}={avg_val:.1f}%")
    avg_overall = sum(avg_scores) / len(avg_scores)
    parts.append(f"Avg={avg_overall:.1f}%")
    print(f"\nOverall: {' | '.join(parts)}")


if __name__ == "__main__":
    main()
