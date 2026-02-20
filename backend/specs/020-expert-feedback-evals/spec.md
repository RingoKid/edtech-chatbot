# 020: Expert Feedback LLM Judge Evals

## Overview

**Status:** 🔲 Not started
**Scope:** Three new LLM judge evals based on expert review of PreK lesson
**Judge Model:** `gpt-5.2` (configurable via `get_chat_model()`)
**Builds on:** Spec 019 (Instructional Quality Evals)
**Source:** Expert review of `prek_letter_b_onlevel` fixture (2026-02-20)
**Standards reference:** `docs/handwriting-spelling-standards.md`

---

## Implementation Checklist

Mark each item ✅ when complete. Work through each eval top-to-bottom before moving to the next.

### Eval 12: `grade_standards`

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Add `StandardItem`, `DevelopmentalCheck`, `GradeStandardsOutput` models | `tests/evals/models.py` | 🔲 |
| 2 | Create rubric (embed standards from `docs/handwriting-spelling-standards.md`, add `{grade}` and `{lesson_output}` placeholders) | `tests/evals/rubrics/grade_standards.md` | 🔲 |
| 3 | Add `run_grade_standards_judge()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 4 | Add `compute_grade_standards_score()` function (composite: 50% standards accuracy + 50% developmental) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 5 | Add `format_grade_standards_detail()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 6 | Add `grade_standards` to `ALL_EVAL_NAMES` and `EVAL_REGISTRY` (with `uses_params: True`) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 7 | Update runner loop to pass `fixture["params"]` when `uses_params` is True | `scripts/run_scaffolding_evals.py` | 🔲 |
| 8 | Verify: run on expert fixture (`expert_prek_letter_z_onlevel`) — expect ≥80% | — | 🔲 |
| 9 | Verify: run on generated fixture (`prek_letter_b_onlevel`) — expect ~0% standards accuracy | — | 🔲 |

### Eval 13: `activity_naming`

| # | Task | File | Status |
|---|------|------|--------|
| 10 | Add `SectionActivityCheck`, `MaterialsCheck`, `ActivityNamingOutput` models | `tests/evals/models.py` | 🔲 |
| 11 | Create rubric (include `{form_d}` and `{lesson_output}` placeholders, define named vs generic) | `tests/evals/rubrics/activity_naming.md` | 🔲 |
| 12 | Add `run_activity_naming_judge()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 13 | Add `compute_activity_naming_score()` function (composite: 60% section naming + 40% materials coverage) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 14 | Add `format_activity_naming_detail()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 15 | Add `activity_naming` to `ALL_EVAL_NAMES` and `EVAL_REGISTRY` (form: `form_d`) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 16 | Verify: run on expert fixture — expect named activities in all 4 sections | — | 🔲 |
| 17 | Verify: run on generated fixture — expect missing Review activity (#5) | — | 🔲 |

### Eval 14: `child_response_coverage`

| # | Task | File | Status |
|---|------|------|--------|
| 18 | Add `InteractionPoint`, `ChildResponseOutput` models | `tests/evals/models.py` | 🔲 |
| 19 | Create rubric (define good/bad response examples, verbal/action rules, `{lesson_output}` placeholder) | `tests/evals/rubrics/child_response_coverage.md` | 🔲 |
| 20 | Add `run_child_response_judge()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 21 | Add `compute_child_response_score()` function (composite: 30% presence + 30% specificity + 40% completeness) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 22 | Add `format_child_response_detail()` function | `scripts/run_scaffolding_evals.py` | 🔲 |
| 23 | Add `child_response_coverage` to `ALL_EVAL_NAMES` and `EVAL_REGISTRY` (form: `none`) | `scripts/run_scaffolding_evals.py` | 🔲 |
| 24 | Verify: run on expert fixture — expect high specificity + completeness | — | 🔲 |
| 25 | Verify: run on generated fixture — expect generic/missing responses | — | 🔲 |

### Final Integration

| # | Task | Status |
|---|------|--------|
| 26 | Run full suite (all 14 evals, no `--eval` flag) — no crashes, all columns populated | 🔲 |
| 27 | Calibration: review judge `evidence`/`reasoning` fields, adjust rubrics if needed | 🔲 |
| 28 | Update this checklist — mark all items ✅ | 🔲 |

### Reference Files (read-only)

| File | Used By |
|------|---------|
| `docs/handwriting-spelling-standards.md` | Embedded in `grade_standards.md` rubric |
| Form D (loaded by `load_form_d()`) | Passed to `activity_naming` judge via `{form_d}` |

---

### Problem

An expert reviewed a generated PreK sound-letter B lesson and identified 11 issues. The existing 11 evals (scaffolding + instructional quality) missed the most fundamental problems:

1. **Wrong standards system** — lesson used Kindergarten GSE codes instead of PreK GELDS codes
2. **No named activities** — sections describe generic actions instead of referencing Form D activities by name
3. **Missing child responses** — interaction points lack specific verbal AND physical responses

These are structural correctness issues that cascade into other failures (wrong standards → wrong developmental expectations → wrong objectives → wrong activities). The current eval suite has no coverage for grade-level appropriateness, activity naming discipline, or response completeness.

### Design Principle

Same pattern as all existing evals (Spec 014/019):

1. **LLM judge extracts structured data** (Pydantic models) — judge handles fuzzy detection, no regex
2. **Scoring function computes a ratio** from the structured data — hard numbers, not vibes grades
3. **Format function renders markdown** for the report

The judge never assigns a score directly. It outputs booleans, counts, and evidence strings. The scoring function does the math.

### Key Reference

The standards reference file at `docs/handwriting-spelling-standards.md` contains the complete filtered standards for all three grade levels:

- **PreK** → GELDS 48-60 month indicators (CLL6, CLL7, CLL8, CLL9, PDM6)
- **Kindergarten** → Georgia K-12 ELA Standards (K.F.PA, K.F.P, K.F.H)
- **1st Grade** → Georgia K-12 ELA Standards (1.F.PA, 1.F.P, 1.F.H)

This file is embedded in the `grade_standards` rubric so the judge has the authoritative standards list.

---

## Eval 12: `grade_standards` — Grade-Appropriate Standards

### Expert Feedback

> #1: "Standards were not PreK"
> #2: "Lesson is not developmentally appropriate for PreK as a result"

### What It Measures

Whether the lesson uses the correct standards system for the specified grade level, lists valid standard codes, and reflects developmentally appropriate expectations. PreK must use GELDS codes (e.g., CLL7.4a). K and 1st must use Georgia K-12 ELA codes (e.g., K.F.P.1.a). The lesson should not expect skills beyond the grade's developmental level.

### How It Works

1. Judge receives lesson output + the grade-level standards reference + the fixture's `grade` parameter
2. Judge checks the Standards section for correct codes
3. Judge checks whether activities and language match the grade's developmental expectations
4. Code computes score from the boolean checklist

### Pydantic Structured Output

**`StandardItem`**

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | The standard code as written in the lesson (e.g., "CLL7.4a" or "ELAGSEKRF3a") |
| `correct_system` | `bool` | Does this code belong to the correct standards system for the grade? (PreK=GELDS, K=K-12 ELA, 1st=K-12 ELA) |
| `valid_code` | `bool` | Is this code a real standard from the reference list (not fabricated)? |
| `relevant_to_handwriting` | `bool` | Is this standard relevant to handwriting/spelling instruction? |
| `reasoning` | `str` | Explanation of the judgment |

**`DevelopmentalCheck`**

| Field | Type | Description |
|-------|------|-------------|
| `criterion` | `str` | What is being checked (e.g., "vocabulary level", "motor expectations") |
| `appropriate` | `bool` | Is this aspect appropriate for the grade? |
| `evidence` | `str` | Quoted text from the lesson supporting the judgment |
| `reasoning` | `str` | Explanation |

**`GradeStandardsOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `grade` | `str` | The grade level being evaluated (from fixture params) |
| `standards` | `list[StandardItem]` | Each standard listed in the lesson's Standards section |
| `developmental_checks` | `list[DevelopmentalCheck]` | Grade-appropriateness checks across the lesson |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Two sub-scores averaged:

1. **Standards accuracy**: count of standards where ALL THREE of (`correct_system`, `valid_code`, `relevant_to_handwriting`) are True, divided by total standards listed. If no standards found, score is 0.

2. **Developmental appropriateness**: count of `appropriate == True` developmental checks, divided by total checks.

**Composite**: `(standards_accuracy × 0.5) + (developmental_appropriateness × 0.5) × 100`

Displayed as `75.0% (Standards: 100.0% 3/3 | Dev: 50.0% 3/6)`.

### Judge Prompt → `tests/evals/rubrics/grade_standards.md`

The rubric prompt should include:

- The full standards reference from `docs/handwriting-spelling-standards.md` — embedded directly in the rubric (not as a variable substitution) so the judge has the authoritative list
- The fixture's grade level passed via `{grade}` substitution
- Clear rules:
  - PreK MUST use GELDS codes (CLL, PDM format). Any ELAGSE or K.F/1.F code is wrong for PreK.
  - K MUST use Georgia K-12 ELA codes (K.F.* format). Any CLL/PDM code is wrong for K.
  - 1st MUST use Georgia K-12 ELA codes (1.F.* format).
- Developmental checks to evaluate (6 items):
  1. **Vocabulary level** — Is the teacher script language appropriate for the age group?
  2. **Motor expectations** — Are fine motor demands realistic? (PreK = finger tracing + large movements before pencil; K = pencil work expected; 1st = fluency)
  3. **Activity complexity** — Are activities at the right cognitive level?
  4. **Response expectations** — Are expected child responses realistic for the age? (PreK = shorter, simpler; 1st = more articulate)
  5. **Session length** — Does the number of activities fit the age group's attention span?
  6. **Prior knowledge assumptions** — Does the lesson assume knowledge appropriate for the grade? (PreK should not assume phoneme segmentation mastery)
- The `{lesson_output}` placeholder

### Report Format

Two tables: **Standards** (per-code accuracy) and **Developmental Appropriateness** (per-criterion checks). Use `+`/`-` for booleans. End with judge summary.

---

## Eval 13: `activity_naming` — Named Form D Activities

### Expert Feedback

> #4: "It did not state the activities and provide a link to a summary of the activities in the sections"
> #5: "It does not include an activity in the review section"

### What It Measures

Whether each scripted lesson section names specific Form D activities from the established repertoire (e.g., "Sound Spark", "Magic Finger Write", "Sound-Letter Hunt", "Trace & Say") rather than describing actions generically. Also checks that the Materials section references the activities used.

### How It Works

1. Judge receives lesson output + Form D (activity reference with names and descriptions)
2. Judge checks each section (1-4) for named Form D activities
3. Judge checks whether Materials section lists the activities
4. Code computes score from per-section results

### Pydantic Structured Output

**`SectionActivityCheck`**

| Field | Type | Description |
|-------|------|-------------|
| `section` | `str` | Which section (e.g., "Review & Connect") |
| `named_activities` | `list[str]` | Form D activity names found in this section (e.g., ["Sound Spark", "Sound Hunt"]) |
| `has_named_activity` | `bool` | Does this section reference at least one Form D activity by name? |
| `generic_descriptions` | `list[str]` | Generic action descriptions found instead of named activities (e.g., ["teacher reviews previously learned sounds"]) |
| `evidence` | `str` | Quoted text showing how the activity is referenced |
| `reasoning` | `str` | Explanation |

**`MaterialsCheck`**

| Field | Type | Description |
|-------|------|-------------|
| `activities_listed` | `list[str]` | Activity names found in the Materials section |
| `activities_in_lesson` | `list[str]` | Activity names found across all scripted sections |
| `missing_from_materials` | `list[str]` | Activities used in the lesson but not listed in Materials |
| `reasoning` | `str` | Explanation |

**`ActivityNamingOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `sections` | `list[SectionActivityCheck]` | One entry per scripted section (1-4) |
| `materials_check` | `MaterialsCheck` | Whether Materials lists the activities used |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Two sub-scores averaged:

1. **Section naming**: count of sections where `has_named_activity == True`, divided by 4 (sections 1-4).

2. **Materials coverage**: count of activities in lesson that also appear in Materials, divided by total unique activities in lesson. If no activities found in lesson, this score is 0.

**Composite**: `(section_naming × 0.6) + (materials_coverage × 0.4) × 100`

Section naming is weighted more heavily because the core problem is unnamed activities in the lesson body.

Displayed as `62.5% (Sections: 75.0% 3/4 | Materials: 50.0% 2/4)`.

### Judge Prompt → `tests/evals/rubrics/activity_naming.md`

The rubric prompt should include:

- Form D content via `{form_d}` substitution — this gives the judge the full repertoire of activity names organized by section and difficulty level
- Clear instructions on what counts as a "named activity":
  - **Named**: "Sound Spark", "Magic Finger Write", "Trace & Say", "Sound Hunt", "Sound-Letter Hunt", "Hide-and-Seek Sound", "Sound Puzzle", etc. — specific activity names from Form D
  - **NOT named**: "teacher reviews sounds", "children practice writing", "teacher demonstrates letter formation" — these are generic descriptions of what happens, not named activities
- The distinction between naming an activity and merely doing what an activity describes. A section might functionally do a Sound Spark activity without ever naming it — that should count as `has_named_activity: false` with a note in `generic_descriptions`
- Instructions to check Materials section separately for activity references
- The `{lesson_output}` placeholder

### Report Format

Two tables: **Section Activity Coverage** (per-section with named activities, generic descriptions, evidence) and **Materials Coverage** (activity vs. listed in Materials). End with judge summary.

---

## Eval 14: `child_response_coverage` — Complete Child Responses

### Expert Feedback

> #9: "There are instances of no child response when there should be. Child response can be both verbal and what they are doing."

### What It Measures

Whether every teacher interaction point (question, prompt, directed activity) has a specific child response. Responses must be specific — not "(Children respond)" — and should include both **verbal** (what children say) and **action** (what children physically do) components where appropriate.

### How It Works

1. Judge receives lesson output
2. Judge identifies all interaction points (teacher questions, prompts, directed activities) in Sections 1-4
3. For each, judge categorizes the response quality
4. Code computes ratios from the categorization

### Pydantic Structured Output

**`InteractionPoint`**

| Field | Type | Description |
|-------|------|-------------|
| `section` | `str` | Which section |
| `teacher_prompt` | `str` | What the teacher says/asks/directs (abbreviated) |
| `prompt_type` | `Literal["question", "directive", "practice_task"]` | Type of interaction: question expects a verbal answer, directive expects an action, practice_task expects both |
| `has_response` | `bool` | Is there ANY child response indicated? |
| `response_text` | `str` | The child response as written (or "none" if missing) |
| `is_specific` | `bool` | Is the response specific enough for a teacher to verify? (vs. generic "(Children respond)") |
| `has_verbal_component` | `bool` | Does the response include what children SAY? |
| `has_action_component` | `bool` | Does the response include what children DO physically? |
| `needs_verbal` | `bool` | Should this interaction have a verbal component? (True for questions and choral responses) |
| `needs_action` | `bool` | Should this interaction have an action component? (True for directives and practice tasks) |
| `reasoning` | `str` | Explanation |

**`ChildResponseOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `interactions` | `list[InteractionPoint]` | All interaction points found in Sections 1-4 |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Three sub-scores:

1. **Response presence**: interactions with `has_response == True` / total interactions

2. **Response specificity**: interactions with `is_specific == True` / interactions with `has_response == True`

3. **Component completeness**: For each interaction, check: if `needs_verbal` then `has_verbal_component` must be True; if `needs_action` then `has_action_component` must be True. Count interactions where all needed components are present / total interactions.

**Composite**: `(presence × 0.3) + (specificity × 0.3) + (completeness × 0.4) × 100`

Component completeness is weighted highest because it's the core of the expert's feedback — responses should include both what children say AND what they do.

Displayed as `66.7% (Present: 90.0% 9/10 | Specific: 77.8% 7/9 | Complete: 50.0% 5/10)`.

### Judge Prompt → `tests/evals/rubrics/child_response_coverage.md`

The rubric prompt should include:

- The expert's feedback context: child responses can be both verbal and action-based
- Examples of good vs. bad responses:
  - **Good verbal**: `(children chorally respond /z/)` — specific sound
  - **Good action**: `(children lift up their zebra card)` — specific physical action
  - **Good combined**: `(children write using dotted lines as guides and say the sequence verbal cues: "Little line across. Slant down the stairs. Little line across.")` — both writing action AND verbal cues
  - **Bad generic**: `(Children respond)`, `(Children answer)`, `(Children do as instructed)`
  - **Bad missing**: Teacher asks a question with no parenthetical response at all
- Rules for `needs_verbal` and `needs_action`:
  - **Questions** (teacher asks something) → `needs_verbal = True` (children should answer)
  - **Directives** (teacher says "do X") → `needs_action = True` (children should perform the action)
  - **Practice tasks** (children write, trace, or produce sounds) → `needs_verbal = True, needs_action = True` (children should do the task AND often say cues/sounds while doing it)
  - **"Say it with me"** type prompts → `needs_verbal = True`
- Evaluate Sections 1-4. Skip Section 5 (Wrap-Up).
- The `{lesson_output}` placeholder

### Report Format

Single table: one row per interaction point, columns for section, teacher prompt, type, has response, specific, verbal/action components, needs verbal/action, response text. End with judge summary.

---

## Runner Integration

### Registry Entries

Add to `ALL_EVAL_NAMES` and `EVAL_REGISTRY`:

| Eval Name | Label | Unit | Form | Substitutions |
|-----------|-------|------|------|--------------|
| `grade_standards` | GradeStd | composite | `none` | `{grade}`, `{lesson_output}` (standards reference baked into rubric) |
| `activity_naming` | ActName | composite | `form_d` | `{form_d}`, `{lesson_output}` |
| `child_response_coverage` | ChildResp | composite | `none` | `{lesson_output}` |

### Implementation Notes

- Follow existing patterns in `run_scaffolding_evals.py` — use Context7 for LangChain/Pydantic docs during implementation
- `grade_standards` is the first eval that needs fixture params beyond lesson text. Add `"uses_params": True` to its registry entry. The runner passes `fixture["params"]` to the judge function, and the rubric uses `{grade}` substitution.
- `activity_naming` reuses `{form_d}` via the existing `load_form_d()` helper
- For composite scores, include sub-scores in the summary table row: `75.0% (Sub1: 80.0% | Sub2: 70.0%)`

---

## Verification

For each eval, run against **expert fixture first** (should score high), then **generated fixture** (should show the gap the expert identified).

| Step | What | Expected |
|------|------|----------|
| 1 | `grade_standards` on expert (`expert_prek_letter_z_onlevel`) | ~100% — uses correct GELDS codes (CLL6.4c, CLL7.4a, CLL9.4d) |
| 2 | `grade_standards` on generated (`prek_letter_b_onlevel`) | ~0% standards accuracy — uses Kindergarten GSE codes for PreK |
| 3 | `activity_naming` on expert vs generated | Expert names activities in every section; generated misses Review (#5) |
| 4 | `child_response_coverage` on expert vs generated | Expert has specific verbal+action responses; generated has generic/missing |
| 5 | Full suite (all 14 evals, no `--eval` flag) | No crashes, all columns populated |

### Calibration

Review `evidence` and `reasoning` fields after each run:
- **Missing things that are present** → rubric needs clearer definitions
- **Crediting things that aren't there** → rubric needs stricter criteria
- **Scoring the expert low** → checklist items may be too strict

Target: expert ≥80%, visible gap between expert and generated scores.

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-20 | Initial draft — 3 new evals from expert feedback (P0 priority) |
