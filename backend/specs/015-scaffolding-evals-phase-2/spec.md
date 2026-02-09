# 015: Scaffolding Evals Phase 2 — Gradual Release & Decomposition

## Overview

**Status:** Implemented
**Scope:** Rubric Criterion 2 — split into two independent evals
**Judge Model:** `gpt-5.2` (configurable via `get_chat_model()`)
**Builds on:** Spec 014 (LLM Judge Evals — Scaffolding Sequencing)

Two new LLM judge evals that extend the scaffolding eval suite. Both correspond to the second rubric criterion:

> "The activities should be organized in a way which reflect logical scaffolding: complex processes are broken down into component parts both within and across activities. The activities should reflect gradual release of support from the teacher."

This criterion contains two independent dimensions, each measured by its own eval:

- `scaffolding_gradual_release` — Does teacher support decrease across the lesson?
- `scaffolding_decomposition` — Are complex tasks broken into sub-skills taught before combining?

---

## Why Two Evals for One Criterion

The rubric bundles two things that are independently measurable:

**Gradual release** measures WHO does the work — does the teacher progressively hand off responsibility? (I do → We do → You do)

**Decomposition** measures WHETHER complex tasks have their prerequisite sub-skills taught first — are all component parts in place before the combined task appears?

A lesson can have perfect gradual release but skip a critical sub-skill (decomposition failure). Or it can teach every sub-skill but never let the teacher step back (release failure). Independent evals catch both.

### Relationship to Existing Evals (Spec 014)

| Eval | What It Measures | Rubric Criterion |
|------|-----------------|------------------|
| `scaffolding_within_activity` (014) | Activities within sections ordered easy → hard | Criterion 1 |
| `scaffolding_between_activity` (014) | Later sections build on earlier section skills | Criterion 1 |
| **`scaffolding_gradual_release` (015)** | **Teacher support decreases across lesson** | **Criterion 2** |
| **`scaffolding_decomposition` (015)** | **Sub-skills taught before complex tasks** | **Criterion 2** |

### Why Not Covered by Existing Evals

**Gradual release vs. difficulty ordering:** The Spec 014 evals check if activities go easier → harder (difficulty). Gradual release checks if teacher support decreases (independence). An activity can get harder without the teacher letting go — these are independent dimensions.

**Decomposition vs. cross-section links:** `scaffolding_between_activity` checks if existing cross-section links are valid. It does NOT check if required links are missing. A lesson could score 100% on `between_activity` (all found links valid) while skipping a critical sub-skill. Decomposition checks for completeness — are ALL necessary sub-skills present?

---

## Reused Infrastructure (from Spec 014)

These new evals reuse the existing system without modification:

| Component | Location | Reused As-Is |
|-----------|----------|-------------|
| 12 pre-generated fixtures | `tests/fixtures/handwriting_generator/*.json` | Yes |
| Form D reference | Loaded at runtime via `load_form_d()` | Yes |
| Judge model call pattern | `get_chat_model()` + `.with_structured_output()` | Yes |
| Rubric template pattern | `{form_d}` and `{lesson_output}` placeholders | Yes |
| Fixture loading utilities | `load_fixture()`, `get_available_fixtures()` | Yes |
| CLI flags | `--fixture`, `--model` | Yes |

---

## Eval 3: `scaffolding_gradual_release`

### What It Measures

Whether teacher support decreases as the lesson progresses — both across sections (2→3→4) and within Section 3 where scaffolding is visibly removed step by step.

### How It Works

1. Judge receives the lesson output + Form D as reference
2. Judge analyzes support levels across sections 2, 3, and 4:
   - Identifies concrete support indicators per section
   - Evaluates whether support decreases at each section transition (2→3, 3→4)
3. Judge analyzes support transitions within Section 3 (Guided Practice):
   - Identifies consecutive steps where scaffolding is removed
   - Evaluates whether each step shows less teacher support
4. Code computes: `transitions_with_decreased_support / total_transitions × 100`

### Section Scope

- **Section 1 (Review & Connect):** Excluded. The gradual release arc starts at Section 2.
- **Section 2 (Model, Explain & Engage):** Peak support — teacher demonstrates everything.
- **Section 3 (Guided Practice):** Shared practice — evaluated both as a section AND internally for step-by-step release.
- **Section 4 (Application):** Lowest support — children apply independently.
- **Section 5 (Wrap-Up):** Excluded per existing convention.

### Support Indicators

The judge identifies concrete indicators from the lesson script:

| Indicator | High Support | Low Support |
|-----------|-------------|------------|
| Who acts first | "My turn" / teacher models | "Your turn" / child goes directly |
| Physical scaffolds | Dotted lines, tracing templates | Blank lines, no guides |
| Starting cues | Start dots, arrows, pre-filled boxes | Empty boxes, open recall |
| Response mode | Choral ("everyone say...") | Individual student response |
| Teacher involvement | Inline correction, hand-over-hand | Peer checking, independent work |
| Task structure | Teacher breaks into micro-steps | Children execute full task sequence |

### Cognitive Load Trade-off

When a later section introduces a new cognitive demand (e.g., phoneme discrimination between /b/ and /p/ in Section 4), it is pedagogically appropriate for teacher support to increase on another dimension (e.g., children trace letters instead of writing independently). This keeps total cognitive load manageable.

Example from the reference lessons:
- Section 3 ends with: Write without tracing (independent motor task)
- Section 4 starts with: Trace the correct letter for /b/ or /p/ (supported motor, but new cognitive demand of discrimination)

This is correct pedagogy for struggling students — the judge should mark this as `support_decreased: true` when:
1. A new cognitive demand was introduced
2. The support increase is on a different dimension than the new demand
3. The overall independence level is appropriate given the student level visible in the lesson

### Student Level Handling

The eval does NOT require a separate `{student_level}` placeholder. The student level is already present in the lesson text (visible through activity choices, scaffolding level, and objectives). The judge reads the lesson and uses the student level as context when evaluating Section 3→4 transitions.

The gradual release metric is the same for all levels — "does support decrease?" — but the judge accounts for cognitive load trade-offs that are more common in struggling-level lessons.

### Pydantic Structured Output

**`SupportLevel`**

| Field | Type | Description |
|-------|------|-------------|
| `section_or_step` | `str` | Section name (e.g., "Model, Explain & Engage") or step name (e.g., "Say and Trace") |
| `support_level` | `Literal["high", "medium", "low"]` | Overall teacher support level |
| `indicators` | `list[str]` | Concrete evidence from the script (e.g., "teacher says 'My turn' before children attempt") |
| `reasoning` | `str` | Why this support level was assigned |

**`SupportTransition`**

| Field | Type | Description |
|-------|------|-------------|
| `from_step` | `str` | Earlier section or step name |
| `to_step` | `str` | Later section or step name |
| `support_decreased` | `bool` | True if the later step has equal or less teacher support (accounting for cognitive load trade-offs) |
| `reasoning` | `str` | Explanation of the support change, including cognitive load considerations if applicable |

**`GradualReleaseOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `across_section_levels` | `list[SupportLevel]` | One entry per section: 2, 3, 4 |
| `across_section_transitions` | `list[SupportTransition]` | Section transitions: 2→3, 3→4 |
| `within_section_levels` | `list[SupportLevel]` | Steps identified inside Section 3 |
| `within_section_transitions` | `list[SupportTransition]` | Consecutive step pairs within Section 3 |
| `explanation` | `str` | Overall summary of gradual release quality |

### Score Computation (in code, not LLM)

```
all_transitions = across_section_transitions + within_section_transitions
total = len(all_transitions)
correct = sum(1 for t in all_transitions if t.support_decreased)
score = (correct / total × 100) if total > 0 else 0.0
```

Returns: `(correct, total, score)` — displayed as `75.0% (3/4)`

### Judge Prompt

**Location:** `tests/evals/rubrics/scaffolding_gradual_release.md`

```markdown
# Gradual Release Scaffolding Judge

## Role

You are an expert in early childhood literacy pedagogy, specializing in handwriting and spelling instruction for PreK through 1st grade. You evaluate whether lesson plans follow the principle of gradual release of responsibility — the progressive transfer of task ownership from teacher to children.

## Task

Analyze the **gradual release of support** in the handwriting lesson below. Determine whether teacher support decreases as the lesson progresses — both across sections and within individual activities.

**Section 1 (Review & Connect) and Section 5 (Wrap-Up) must be excluded from your analysis.** The gradual release arc starts at Section 2 (Model, Explain & Engage) and ends at Section 4 (Application).

## Rubric Criterion

> "The activities should be organized in a way which reflect logical scaffolding: complex processes are broken down into component parts both within and across activities. The activities should reflect gradual release of support from the teacher."

### What "Gradual Release" Looks Like

**Across sections (I do → We do → You do):**
- Section 2 (Model): Teacher demonstrates everything. "Watch me." "My turn." Children observe and repeat.
- Section 3 (Guided Practice): Children do it WITH teacher support. Tracing, dots, verbal cues guide them.
- Section 4 (Application): Children apply skills with minimal teacher help. "Your turn."

**Within Section 3 (scaffolding removal):**
- Step 1: Say and Trace — children trace dotted lines with a pencil, saying stroke cues aloud
- Step 2: Write with start dot — only a dot shows where to begin, no dotted path
- Step 3: Write independently — nothing on the page, children write from memory

The scaffolding (dots, lines, guides) literally disappears from step to step.

### Support Indicators

Use these concrete indicators to assess support level at each point:

| Indicator | High Support | Low Support |
|-----------|-------------|------------|
| Who acts first | "My turn" / teacher models before children try | "Your turn" / children go directly |
| Physical scaffolds | Dotted lines, tracing templates, textured cards | Blank lines, no visual guides |
| Starting cues | Start dots, arrows, pre-filled answer boxes | Empty boxes, open recall |
| Response mode | Choral response ("everyone say...") | Individual student response |
| Teacher involvement | Inline correction, hand-over-hand guidance | Peer checking, independent work |
| Task structure | Teacher breaks task into micro-steps for children | Children execute full task sequence independently |

### Cognitive Load Trade-off

Important: When a later section introduces a new cognitive demand (e.g., discriminating between /b/ and /p/ in Section 4), it is pedagogically appropriate for teacher support to increase on another dimension (e.g., children trace letters instead of writing independently). This keeps total cognitive load manageable.

When evaluating a transition where support appears to increase, check whether:
1. A new cognitive demand was introduced in the later step
2. The support increase is on a different dimension than the new demand
3. The overall independence level is appropriate given the student level visible in the lesson

If all three are true, mark the transition as `support_decreased: true` — the apparent increase is a justified cognitive load trade-off, not a failure of gradual release.

## Form D — Activity Reference

{form_d}

## Instructions

For the lesson below:

1. **Identify sections 2, 3, and 4** (Model Explain & Engage, Guided Practice, Application). Skip sections 1 and 5.
2. **Across-section analysis:**
   a. For each section (2, 3, 4), assess the overall teacher support level (high, medium, low)
   b. List concrete indicators from the lesson script that evidence this level
   c. For each transition (2→3, 3→4), determine whether support decreased
3. **Within-section analysis (Section 3 only):**
   a. Identify all distinct steps or sub-activities within Guided Practice
   b. For each step, assess the support level (high, medium, low)
   c. For each consecutive pair of steps, determine whether support decreased
4. **Provide reasoning** for every support level assignment and every transition judgment. Reference specific quotes or activities from the lesson script.

## Lesson to Evaluate

{lesson_output}
```

---

## Eval 4: `scaffolding_decomposition`

### What It Measures

Whether the complex tasks in later sections (Sections 3-4) have their component sub-skills explicitly taught in earlier sections. Checks for completeness — are ALL necessary sub-skills in place before children are asked to perform the combined task?

### How It Works

1. Judge receives the lesson output + Form D as reference
2. Judge identifies complex tasks in Sections 3 and 4 — activities that require multiple component skills
3. For each complex task, judge determines what sub-skills are required (using Form D as reference for skill relationships)
4. Judge checks if each sub-skill is explicitly taught in an earlier section
5. Code computes: `components_taught / total_components_required × 100`

### What Counts as a "Complex Task"

Activities in Sections 3-4 that combine multiple skills. Identified by Form D difficulty level (middle and high activities are typically composite) and by the nature of the task:

- **Spelling a word** requires: hearing sounds, segmenting, matching sounds to letters, writing letters
- **Writing a letter correctly** requires: knowing the sound-letter connection, knowing stroke sequence, motor execution on lines
- **Sound-Letter Hunt** requires: hearing the word, identifying the target sound, matching to letter, writing the letter

### What Counts as a "Component Sub-skill"

A foundational skill that the complex task depends on. The judge uses Form D to understand skill hierarchies:

- **Low-level** activities (tap, point, pronounce) = foundational perceptual skills
- **Middle-level** activities (trace, follow dots, segment) = guided production skills
- **High-level** activities (write independently, spell, substitute) = combined skills

A component is "taught" if there is a specific activity, teacher modeling, or structured practice in an earlier section that explicitly addresses it.

### Pydantic Structured Output

**`ComponentSkill`**

| Field | Type | Description |
|-------|------|-------------|
| `skill_name` | `str` | Name of the component skill (e.g., "sound segmentation") |
| `is_taught` | `bool` | Whether this skill is explicitly taught before the complex task |
| `taught_in_section` | `str \| None` | Section name where it's taught, or None if missing |
| `taught_via_activity` | `str \| None` | Activity name that teaches it, or None if missing |
| `reasoning` | `str` | What the sub-skill is and where/whether it appears |

**`ComplexTask`**

| Field | Type | Description |
|-------|------|-------------|
| `task_name` | `str` | Name of the complex activity (e.g., "Stretch and Spell") |
| `section` | `str` | Section where it appears (e.g., "Application") |
| `required_components` | `list[ComponentSkill]` | All component sub-skills this task requires |

**`DecompositionOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `complex_tasks` | `list[ComplexTask]` | All complex tasks identified in Sections 3-4 |
| `explanation` | `str` | Overall summary of decomposition quality |

### Score Computation (in code, not LLM)

```
total_components = sum(len(t.required_components) for t in complex_tasks)
covered = sum(1 for t in complex_tasks for c in t.required_components if c.is_taught)
score = (covered / total_components × 100) if total_components > 0 else 0.0
```

Returns: `(covered, total_components, score)` — displayed as `83.3% (10/12)`

### Judge Prompt

**Location:** `tests/evals/rubrics/scaffolding_decomposition.md`

```markdown
# Decomposition Scaffolding Judge

## Role

You are an expert in early childhood literacy pedagogy, specializing in handwriting and spelling instruction for PreK through 1st grade. You evaluate whether lesson plans properly decompose complex tasks into component sub-skills that are taught before children are asked to perform the combined task.

## Task

Analyze the **process decomposition** in the handwriting lesson below. Determine whether the complex tasks in later sections (especially Section 4 — Application) have their component sub-skills explicitly taught in earlier sections.

**Section 5 (Wrap-Up) must be excluded from your analysis.**

## Rubric Criterion

> "The activities should be organized in a way which reflect logical scaffolding: complex processes are broken down into component parts both within and across activities."

### What "Decomposition" Looks Like

Complex tasks in Sections 3-4 require multiple sub-skills. A well-decomposed lesson teaches each sub-skill in earlier sections before combining them.

**Example 1 — Spelling a CVC word (Application: Stretch and Spell):**

| Component Skill | Where It Should Be Taught | Example Activity |
|----------------|--------------------------|-----------------|
| Hear/identify target sound | Section 1 (Review) or Section 2 (Model) | Sound Spark, Tap that Sound |
| Segment word into individual sounds | Section 2 (Model) | Stretch the Sounds, How Many Sounds |
| Match each sound to its letter | Section 2 (Model) | Teacher modeling, Spell Aloud |
| Write the letter with correct formation | Section 3 (Guided Practice) | Trace & Say, Magic Finger Write |
| **Combined: segment + write all letters** | **Section 4 (Application)** | **Stretch and Spell** |

If the lesson asks children to spell CVC words in Section 4 but never teaches sound segmentation in Section 2, a critical sub-skill is missing.

**Example 2 — Writing the target letter in context (Application: Sound-Letter Hunt):**

| Component Skill | Where It Should Be Taught | Example Activity |
|----------------|--------------------------|-----------------|
| Identify target sound in spoken words | Section 2 (Model) | Sound Hunt |
| Know letter formation strokes | Section 2 (Model) | Teacher models with verbal cues |
| Practice letter formation | Section 3 (Guided Practice) | Say and Trace, Write and Sound |
| **Combined: hear word → identify sound → write letter** | **Section 4 (Application)** | **Sound-Letter Hunt** |

### How to Identify Component Skills

Use Form D to understand what skills each activity requires. Higher-level activities build on lower-level skills:

- **Low-level** activities (tap, point, pronounce) = foundational perceptual skills
- **Middle-level** activities (trace, follow dots, segment) = guided production skills
- **High-level** activities (write independently, spell, substitute sounds) = combined skills requiring multiple foundations

A component skill is "taught" if there is a specific activity, teacher modeling, or structured practice in an earlier section that explicitly addresses it. Merely mentioning a skill in passing does not count — the lesson must give children an opportunity to practice or observe the skill.

## Form D — Activity Reference (Difficulty Labels)

{form_d}

## Instructions

For the lesson below:

1. **Identify the complex tasks** in Sections 3 and 4 (Guided Practice and Application). These are activities that require multiple component skills to perform. Use Form D difficulty labels as a guide — middle-level and high-level activities are typically composite.
2. **For each complex task**, determine what component sub-skills are required. Reference Form D to understand skill relationships.
3. **Check if each component skill is explicitly taught** in an earlier section. Look for specific activities, teacher modeling, or structured practice that addresses the sub-skill.
4. **Mark each component** as taught (with section name and activity name) or missing (with explanation of what's absent).
5. **Provide reasoning** for each judgment — explain what the sub-skill is and where (or if) it appears earlier in the lesson.

## Lesson to Evaluate

{lesson_output}
```

---

## Report Generation Changes

### Extended Summary Table

The summary table expands from 2 eval columns to 4:

```markdown
| Fixture | Within | Across | Release | Decomp | Avg |
|---------|--------|--------|---------|--------|-----|
| prek_letter_z_onlevel | 87.5% (7/8) | 100% (4/4) | 75.0% (3/4) | 83.3% (5/6) | 86.5% |
| k_letter_b_struggling | 100% (5/5) | 80.0% (4/5) | 100% (4/4) | 100% (8/8) | 95.0% |
| ... | ... | ... | ... | ... | ... |
| **Overall Average** | **82.3%** | **88.5%** | **85.0%** | **90.0%** | **86.5%** |
```

Average is now the mean of all 4 eval scores.

### Per-Fixture Detail Sections

Each fixture's detail section adds two new subsections:

**Gradual Release detail:**

```markdown
#### Gradual Release: 75.0% (3/4 transitions)

**Across-Section Support Levels**
| Section | Support Level | Indicators |
|---------|-------------|------------|
| Model, Explain & Engage | high | "Watch me", teacher models first, choral response |
| Guided Practice | medium | Dotted lines for tracing, "Say and write" |
| Application | low | "Your turn", empty boxes, independent writing |

**Across-Section Transitions**
| # | From | To | Released? | Reasoning |
|---|------|----|----------|-----------|
| 1 | Model (high) | Guided (medium) | + | "Teacher shifts from demonstration to shared practice" |
| 2 | Guided (medium) | Application (low) | + | "Children now apply independently" |

**Within Section 3 (Guided Practice)**
| # | From | To | Released? | Reasoning |
|---|------|----|----------|-----------|
| 1 | Magic Finger Write (high) | Say and Trace (medium) | + | "Finger tracing → pencil with dots" |
| 2 | Say and Trace (medium) | Write and Sound (low) | - | "Still has teacher monitoring, support didn't decrease" |

**Judge Summary:** "..."
```

**Decomposition detail:**

```markdown
#### Decomposition: 83.3% (5/6 components)

| Complex Task (Section) | Component Skill | Taught? | Where | Reasoning |
|------------------------|----------------|---------|-------|-----------|
| Stretch & Spell (§4) | Sound identification | + | Sound Hunt (§2) | "Children identify /b/ in words" |
| Stretch & Spell (§4) | Sound segmentation | + | Stretch the Sounds (§2) | "Segmenting words into phonemes" |
| Stretch & Spell (§4) | Sound-letter mapping | - | — | "No explicit mapping practice before spelling" |
| Stretch & Spell (§4) | Letter formation | + | Say and Trace (§3) | "Practiced writing the letter" |
| Sound-Letter Hunt (§4) | Sound identification | + | Sound Hunt (§2) | "Same skill, same section" |
| Sound-Letter Hunt (§4) | Letter writing | + | Say and Trace (§3) | "Practiced letter formation" |

**Judge Summary:** "..."
```

---

## Criteria Registry Updates

Add both new criteria to `CRITERIA_REGISTRY` in `app/langfuse/criteria.py`:

```python
"scaffolding_gradual_release": {
    "type": "llm-judge",
    "description": "Checks if teacher support decreases across the lesson (I do → We do → You do)",
},
"scaffolding_decomposition": {
    "type": "llm-judge",
    "description": "Checks if complex tasks have prerequisite sub-skills taught in earlier sections",
},
```

---

## Runner Script Changes

**File:** `scripts/run_scaffolding_evals.py`

### New Imports

Add the two new Pydantic output models from `tests/evals/models.py`.

### New Functions

| Function | Purpose |
|----------|---------|
| `run_release_judge(lesson_output, model_key, form_d)` | Run gradual release judge. Load rubric `scaffolding_gradual_release`, substitute placeholders, call `.with_structured_output(GradualReleaseOutput)` |
| `run_decomposition_judge(lesson_output, model_key, form_d)` | Run decomposition judge. Load rubric `scaffolding_decomposition`, substitute placeholders, call `.with_structured_output(DecompositionOutput)` |
| `compute_release_score(output)` | Count transitions where `support_decreased == True`. Return `(correct, total, percentage)` |
| `compute_decomposition_score(output)` | Count components where `is_taught == True`. Return `(covered, total, percentage)` |
| `format_release_detail(output)` | Format gradual release output as markdown tables (support levels + transitions) |
| `format_decomposition_detail(output)` | Format decomposition output as markdown tables (complex tasks + components) |

### Main Loop Changes

The per-fixture loop runs 4 judges instead of 2:

```
for fixture_id in fixture_ids:
    load fixture
    run within_judge        (existing)
    run across_judge        (existing)
    run release_judge       (new)
    run decomposition_judge (new)
    compute all 4 scores
    store results
```

### Report Changes

- Summary table: 4 eval columns + average
- Per-fixture detail: 4 subsections (within, across, release, decomposition)
- Console output: all 4 scores per fixture

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `tests/evals/rubrics/scaffolding_gradual_release.md` | Judge prompt for gradual release eval |
| `tests/evals/rubrics/scaffolding_decomposition.md` | Judge prompt for decomposition eval |

### Modified Files

| File | Changes |
|------|---------|
| `tests/evals/models.py` | Add `SupportLevel`, `SupportTransition`, `GradualReleaseOutput`, `ComponentSkill`, `ComplexTask`, `DecompositionOutput` |
| `scripts/run_scaffolding_evals.py` | Add 2 judge functions, 2 compute functions, 2 format functions; extend main loop and report generation |
| `app/langfuse/criteria.py` | Add 2 new `llm-judge` entries to `CRITERIA_REGISTRY` |

### Unchanged Files

| File | Notes |
|------|-------|
| `tests/fixtures/handwriting_generator/*.json` | Same 12 fixtures, reused as-is |
| `scripts/generate_eval_fixtures.py` | No changes needed |
| `tests/evals/rubrics/scaffolding_within_activity.md` | Unchanged |
| `tests/evals/rubrics/scaffolding_between_activity.md` | Unchanged |

---

## Verification

### Run All 4 Evals

```bash
docker compose exec backend python scripts/run_scaffolding_evals.py
# Expected: Markdown report with 4 eval columns in summary table
```

### Single Fixture Test

```bash
docker compose exec backend python scripts/run_scaffolding_evals.py --fixture k_letter_b_onlevel
# Expected: Report with 4 eval scores for one fixture
```

### Verify Report Contents

The report should contain:
- Summary table with Within, Across, Release, Decomp columns and averages
- Per-fixture gradual release detail: support levels + transition tables
- Per-fixture decomposition detail: complex tasks + component skills table
- Judge reasoning quoted for every transition and component
- Both fractions and percentages (e.g., `75.0% (3/4)`)

### Verify Criteria Registry

```bash
docker compose exec backend python -c "from app.langfuse.criteria import CRITERIA_REGISTRY; print([k for k in CRITERIA_REGISTRY if 'scaffolding' in k])"
# Expected: ['scaffolding_within_activity', 'scaffolding_between_activity', 'scaffolding_gradual_release', 'scaffolding_decomposition']
```

---

## Implementation Notes

- Use Context7 MCP to pull latest documentation for LangChain, LangGraph, and Pydantic during implementation
- Use `get_chat_model("gpt-5.2")` from `app/llm/client.py` for judge calls
- Use `model.with_structured_output(PydanticModel)` for structured judge output
- Judge rubric templates use two placeholders substituted at runtime: `{form_d}` (loaded from source markdown) and `{lesson_output}` (from fixture JSON)
- Form D is loaded once per eval run from the source markdown file — not hardcoded in rubric files
- Follow the existing patterns in `run_scaffolding_evals.py` for the new judge/compute/format functions
- The `|` characters in judge reasoning must be escaped in markdown tables (existing pattern: `.replace("|", "\\|")`)

---

## Design Decisions

See `backend/specs/014-llm-judge-evals/decisions.md` for foundational decisions (fixture-based approach, scoring methodology, separate evals). Key decisions specific to this spec:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Split criterion 2 into two evals | Gradual release + decomposition | Independent dimensions; a lesson can fail one while passing the other |
| Gradual release scope | Sections 2→3→4 + within Section 3 | Section 2 is peak support, Section 4 is lowest; Section 3 has the clearest within-activity release |
| Cognitive load trade-off | Judge instruction, not level-aware logic | Student level is already in the lesson text; simple instruction handles the edge case |
| Decomposition anchored on Sections 3-4 | Trace backward from complex tasks | Application tasks are the "end goals" — check if foundations are laid |
| No `{student_level}` placeholder | Judge reads level from lesson content | Avoids adding a third placeholder; level info is already in the lesson text |
| Same fixtures, same runner | Extend existing script | Avoids parallel infrastructure; one report with all 4 evals |

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic models (6 new) | ✅ Done | `tests/evals/models.py` |
| Gradual release rubric | ✅ Done | `tests/evals/rubrics/scaffolding_gradual_release.md` |
| Decomposition rubric | ✅ Done | `tests/evals/rubrics/scaffolding_decomposition.md` |
| Runner script (4 evals) | ✅ Done | `scripts/run_scaffolding_evals.py` |
| Criteria registry | ✅ Done | `app/langfuse/criteria.py` |
| End-to-end verification | ✅ Done | Single fixture: 4 evals scored successfully |

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-07 | Initial draft — gradual release + decomposition evals |
| 0.2 | 2026-02-08 | Implemented — all components built and verified |
