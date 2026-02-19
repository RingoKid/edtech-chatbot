# 019: Instructional Quality LLM Judge Evals

## Overview

**Status:** 🔲 Not started
**Scope:** Five new LLM judge evals for instructional quality
**Judge Model:** `gpt-5.2` (configurable via `get_chat_model()`)
**Builds on:** Spec 014/015 (Scaffolding Evals), Spec 018 (Verbatim & Structure Evals)
**Source rubric:** `prompt/Handwriting & Spelling (Transcription) AI Codes/Rubric for Lesson Plan Generator.md`

### Problem

The existing 6 evals (within, across, release, decomposition, verbatim, structure) measure **pedagogical architecture** — whether scaffolding is structured correctly, sections build on each other, and support decreases. They score generated lessons at ~93% average.

But generated lessons are significantly thinner than expert-written ones. The generator gets the structure right but produces **summarized stage directions** instead of **verbatim read-aloud scripts**. Key instructional moves are missing: think-alouds, corrective feedback, post-response explanations, sound comparisons. The existing evals cannot detect this gap.

These 5 new evals target the **instructional quality criteria** from the expert rubric that are currently unmeasured.

### Design Principle

All 5 evals follow the same pattern as existing evals:

1. **LLM judge extracts structured data** (Pydantic models) — the judge handles fuzzy detection, no regex
2. **Scoring function computes a ratio** from the structured data — hard numbers, not vibes grades
3. **Format function renders markdown** for the report

The judge never assigns a score directly. It outputs booleans and counts. The scoring function does the math.

---

## Eval 7: `think_aloud` — Detailed Modeling

### Rubric Criterion

> "The generated lesson plan should always provide detailed modeling or a link for example detailed modeling. Detailed modeling is not just demonstrating directions to a task. It is detailing what is happening in the thinking process to complete a task."

### What It Measures

Whether sections that require independent student work (Sections 3-4) include a teacher **worked example with visible thinking** before students attempt the task. A think-aloud is the teacher narrating their internal reasoning out loud, step by step — not just giving directions.

### How It Works

1. Judge receives lesson output + the rubric criterion with its expert example
2. Judge identifies each section (3 and 4) where students must perform a task independently
3. For each, judge evaluates 5 checklist items about the teacher's worked example
4. Code computes score from the boolean checklist

### Pydantic Structured Output

**`ThinkAloudInstance`**

| Field | Type | Description |
|-------|------|-------------|
| `section` | `str` | Which section (e.g., "Application") |
| `task_description` | `str` | What students are asked to do independently |
| `worked_example_present` | `bool` | Does the teacher do a full worked example before students try? |
| `uses_specific_word` | `bool` | Does the example use a specific word (e.g., "zebra"), not a generic placeholder? |
| `narrates_reasoning` | `bool` | Does the teacher narrate internal thinking ("I am thinking...", "So I know...", "I hear...")? |
| `shows_steps_sequentially` | `bool` | Does the teacher walk through each step of the process one at a time? |
| `connects_sound_to_letter` | `bool` | Does the teacher explicitly link the sound to its letter ("the /z/ sound is written with letter z")? |
| `evidence` | `str` | Quoted text from the lesson supporting the judgment |

**`ThinkAloudOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `instances` | `list[ThinkAloudInstance]` | One entry per section requiring independent student work (expect 1-2) |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Per instance: count of True values among `worked_example_present`, `uses_specific_word`, `narrates_reasoning`, `shows_steps_sequentially`, `connects_sound_to_letter` → divide by 5.

If multiple instances, average across them. If `worked_example_present` is False, the other 4 are automatically False (you can't have reasoning without an example).

Displayed as `60.0% (3/5 items)`.

### Judge Prompt → `tests/evals/rubrics/think_aloud.md`

The rubric prompt should include:

- The rubric criterion quoted from the expert rubric (criterion #9)
- The expert example from the rubric: *"Let me show you. My turn. The word is cab. So, I first stretch the sounds, c-a-b, the beginning sound is /c/. I know that the /c/ sound is written with the letter c..."*
- Clear instructions distinguishing a **think-aloud** (narrates reasoning) from **task directions** (tells students what to do)
- The 5 checklist items as the judge's evaluation criteria
- Sections to evaluate: 3 (Guided Practice) and 4 (Application). Skip Sections 1, 2, and 5

### Report Format

```markdown
#### Think-Aloud: 60.0% (3/5 items)

| Section | Task | Example? | Specific Word? | Narrates? | Steps? | Sound→Letter? | Evidence |
|---------|------|----------|----------------|-----------|--------|---------------|----------|
| Application | Sound-Letter Hunt | + | + | + | - | - | "I am going to say a word..." |

**Judge Summary:** "..."
```

---

## Eval 8: `corrective_feedback` — Anticipating Errors

### Rubric Criterion

> "The generated lesson should include considerations of where young children may make errors and provide possible corrective feedback."

### What It Measures

Whether the lesson anticipates specific, plausible errors children might make with the target letter/sound and scripts a teacher response that addresses the error.

### How It Works

1. Judge receives lesson output + rubric criterion with expert example
2. Judge searches the entire lesson for corrective feedback blocks
3. For each block found, judge evaluates 4 checklist items
4. If no blocks found, score is 0/4
5. Code computes score from the checklist

### Pydantic Structured Output

**`CorrectiveFeedbackBlock`**

| Field | Type | Description |
|-------|------|-------------|
| `location` | `str` | Which section it appears in |
| `anticipated_error` | `str` | What error is described (e.g., "children may write s instead of z") |
| `is_plausible` | `bool` | Is this a realistic error for this letter/sound/grade level? |
| `has_scripted_response` | `bool` | Does the teacher correction include actual dialogue (not just "correct if needed")? |
| `explains_difference` | `bool` | Does the correction explain WHY the student's answer is wrong or how to distinguish correct from incorrect? |
| `engages_students` | `bool` | Does the correction involve students (e.g., "try both sounds", "what's different?") rather than just telling them? |
| `evidence` | `str` | Quoted text from the lesson |

**`CorrectiveFeedbackOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `blocks` | `list[CorrectiveFeedbackBlock]` | All corrective feedback found (empty list if none) |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

If `blocks` is empty: `0/4`.

If blocks exist: for the best block, count True values among `is_plausible`, `has_scripted_response`, `explains_difference`, `engages_students` → divide by 4.

Displayed as `75.0% (3/4 items)`.

### Judge Prompt → `tests/evals/rubrics/corrective_feedback.md`

The rubric prompt should include:

- The rubric criterion quoted from the expert rubric (criterion #8)
- The expert example: the b/d reversal corrective feedback script from the rubric
- Instructions to search the **entire lesson** (all 5 sections), not just a specific one
- The 4 checklist items as evaluation criteria
- Clarify that generic phrases like "correct if needed" or "provide feedback" do NOT count as scripted corrective feedback

### Report Format

```markdown
#### Corrective Feedback: 75.0% (3/4 items)

| Location | Error Anticipated | Plausible? | Scripted? | Explains? | Engages? | Evidence |
|----------|-------------------|------------|-----------|-----------|----------|----------|
| Model, Explain & Engage | children may confuse z/s voicing | + | + | + | - | "Some children may..." |

**Judge Summary:** "..."
```

---

## Eval 9: `post_response` — Explaining Why

### Rubric Criterion

> "The generated lesson plan should include explanations to children why their answer is correct after the first and/or second elicited response from children during an activity"

### What It Measures

Whether the teacher explains WHY a student's answer is correct after the first 1-2 student responses in each activity — not just confirming with "Right" or "Yes."

### How It Works

1. Judge receives lesson output + rubric criterion with expert example
2. Judge identifies all activities across Sections 1-4 that include student responses
3. For each activity, judge evaluates the first 2 student responses: is each followed by a confirmation only ("Right.") or an explanation ("Right, because...")?
4. Code computes the ratio of explanations to total evaluated responses

### Pydantic Structured Output

**`StudentResponse`**

| Field | Type | Description |
|-------|------|-------------|
| `response_text` | `str` | What students said/did (e.g., "children say /z/") |
| `followed_by` | `Literal["explanation", "confirmation_only", "nothing"]` | What the teacher says after |
| `teacher_text` | `str` | The actual teacher response text |

**`ActivityResponses`**

| Field | Type | Description |
|-------|------|-------------|
| `section` | `str` | Which section |
| `activity_name` | `str` | Name of the activity |
| `first_two_responses` | `list[StudentResponse]` | The first 1-2 student responses in this activity (max 2) |

**`PostResponseOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `activities` | `list[ActivityResponses]` | All activities with student responses in Sections 1-4 |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Collect all `StudentResponse` entries across all activities. Count how many have `followed_by == "explanation"`. Divide by total responses evaluated, with a **minimum response floor of 3**. If fewer than 3 responses are found, use 3 as the denominator to prevent sparse lessons from scoring artificially high (e.g., 1 explanation out of 1 found → 1/3 = 33%, not 1/1 = 100%).

Displayed as `33.3% (1/3 responses)` when floored, or `83.3% (5/6 responses)` when above the floor.

### Judge Prompt → `tests/evals/rubrics/post_response_explanation.md`

The rubric prompt should include:

- The rubric criterion quoted from the expert rubric (criterion #4)
- The expert example: *"Does /b/-et start with the /b/ or /p/ sound? (children should say /b/) Yes. I am pushing out air and using my vocal box /b/, so I am going to hold up my ball sound card for the /b/ sound."*
- Clear distinction between the three categories:
  - **explanation**: teacher says WHY the answer is correct ("Right, because zebra starts with /z/")
  - **confirmation_only**: teacher acknowledges without reasoning ("Right." / "Yes." / "Good.")
  - **nothing**: teacher moves directly to next step with no acknowledgment
- Only evaluate the **first 2 student responses per activity** (per the rubric: "after the first and/or second elicited response")
- Evaluate Sections 1-4 only. Skip Section 5 (Wrap-Up)

### Report Format

```markdown
#### Post-Response Explanation: 33.3% (2/6 responses)

| Section | Activity | Response | Followed By | Teacher Text |
|---------|----------|----------|-------------|--------------|
| Model, Explain & Engage | Sound Hunt | children say /z/ | confirmation_only | "Right." |
| Model, Explain & Engage | Articulation | children respond yes | explanation | "That means you are using your voice..." |

**Judge Summary:** "..."
```

---

## Eval 10: `sound_comparison` — Comparing Confusable Pairs

### Rubric Criteria

> "When appropriate, the activity examples should pair sounds and letters in a way that can support children's comparing and contrasting of phonemes and letter forms for deeper processing."

> "Examples of sounds and letter forms should also include high-level analysis of sounds and forms through comparing and contrasting."

### What It Measures

Whether the lesson compares the target sound/letter with a confusable partner (e.g., /z/ with /s/, or letter b with letter d) and teaches students how they are similar and different.

### How It Works

1. Judge receives lesson output + rubric criteria with expert examples
2. Judge searches the lesson for any comparison between the target sound/letter and another sound/letter
3. If found, judge evaluates 4 checklist items about the comparison quality
4. Code computes score from the checklist

### Pydantic Structured Output

**`ComparisonBlock`**

| Field | Type | Description |
|-------|------|-------------|
| `location` | `str` | Which section |
| `target` | `str` | Target sound/letter (e.g., "/z/" or "letter z") |
| `compared_with` | `str` | The confusable partner (e.g., "/s/" or "letter s") |
| `describes_similarity` | `bool` | Does the lesson describe how the two are similar? |
| `describes_difference` | `bool` | Does the lesson describe how the two differ? |
| `includes_articulatory_detail` | `bool` | Does the comparison include mouth/lip/tongue/voicing descriptions? |
| `students_produce_both` | `bool` | Do students actively try producing or writing both sounds/letters? |
| `evidence` | `str` | Quoted text from the lesson |

**`SoundLetterComparisonOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `comparisons` | `list[ComparisonBlock]` | All comparison blocks found (empty list if none) |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

If `comparisons` is empty: `0/4`.

If comparisons exist: for the best block, count True values among `describes_similarity`, `describes_difference`, `includes_articulatory_detail`, `students_produce_both` → divide by 4.

Displayed as `50.0% (2/4 items)`.

### Judge Prompt → `tests/evals/rubrics/sound_letter_comparison.md`

The rubric prompt should include:

- Both rubric criteria quoted from the expert rubric (criteria #6 and #11)
- The expert example: the /b/ vs /p/ comparison script from the rubric
- Instructions that "comparing and contrasting" can appear as:
  - Explicit instruction (dedicated comparison activity)
  - Embedded in activities (Sound Hunt using both sounds)
  - Corrective feedback (addressing confusion between similar letters)
- The 4 checklist items as evaluation criteria
- Evaluate the entire lesson (all sections)

### Report Format

```markdown
#### Sound/Letter Comparison: 50.0% (2/4 items)

| Location | Target | Compared With | Similarity? | Difference? | Articulatory? | Students Produce? | Evidence |
|----------|--------|---------------|-------------|-------------|---------------|-------------------|----------|
| Model, Explain & Engage | /z/ | /s/ | + | + | - | - | "Remember that /z/ is like /s/..." |

**Judge Summary:** "..."
```

---

## Eval 11: `script_specificity` — Dialogue vs. Stage Directions

### Rubric Criterion

> "The generated lesson plan should provide detailed explanations for students to clearly understand a skill, concept, or process. For sounds, this involves pronunciation practice, and use of gesture to support cementing sound to memory. For letters specific sequenced verbal cues."

### What It Measures

Whether the teacher script contains **actual verbatim dialogue** a teacher can read aloud, or **summarized stage directions** that require the teacher to improvise. This eval measures script density per section.

### How It Works

1. Judge receives lesson output + rubric criterion with expert examples
2. Judge analyzes each section (1-4) and counts dialogue vs. stage directions
3. Judge also counts specific example words and categorizes child responses
4. Code computes ratios from the counts

### Pydantic Structured Output

**`SectionSpecificity`**

| Field | Type | Description |
|-------|------|-------------|
| `section` | `str` | Which section |
| `dialogue_lines` | `int` | Count of lines with actual quoted/scripted teacher speech |
| `stage_directions` | `int` | Count of summarized descriptions (e.g., "{Teacher reads words...}", "Teacher guides students") |
| `specific_example_words` | `list[str]` | Specific words used as examples in sound activities (e.g., ["zebra", "tiger"]) |
| `specific_child_responses` | `int` | Child responses with actual content (e.g., "children say /z/") |
| `generic_child_responses` | `int` | Generic child responses (e.g., "children respond", "children answer") |
| `has_pacing_cues` | `bool` | Does the section include pacing/management cues (e.g., "Ready. Go.", "My turn. Your turn.")? |
| `evidence_sample` | `str` | Representative excerpt showing the section's specificity level |

**`ScriptSpecificityOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `sections` | `list[SectionSpecificity]` | One entry per section (1-4) |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

Three sub-metrics computed from the judge's counts:

1. **Dialogue (volume-adjusted)**: Per-section, compute `(dialogue_lines / (dialogue_lines + stage_directions)) × min(1.0, dialogue_lines / 10)`. Average across sections. The **volume floor of 10** dialogue lines per section (conservative — expert average is ~16/section) prevents a section with 2 dialogue lines and 0 directions from scoring the same as one with 30 dialogue lines and 5 directions. The ratio alone is a purity metric; the volume scale makes it a combined purity × volume metric.
2. **Example word count**: `sum(len(specific_example_words))` across all sections (raw count, not a ratio)
3. **Response specificity**: `sum(specific_child_responses) / sum(specific_child_responses + generic_child_responses)` across all sections

**Composite score**: `(volume_adjusted_dialogue × 0.5) + (response_specificity × 0.3) + (pacing_score × 0.2)` where `pacing_score` = sections with pacing cues / 4.

Displayed as `72.5%` with sub-metric breakdown: `Dialogue (vol-adj): 80.0% | Examples: 5 words | Responses: 66.7% | Pacing: 3/4`

### Judge Prompt → `tests/evals/rubrics/script_specificity.md`

The rubric prompt should include:

- The rubric criterion quoted from the expert rubric (criterion #10)
- Expert example showing the difference between verbatim script and stage direction:
  - **Verbatim**: `"Ready. My Turn. {Teacher points to /m/} Get Ready. Go." (children chorally respond /m/).`
  - **Stage direction**: `{Teacher reads words with previously learned sounds, prompting students to identify the initial sound.}`
- Clear counting instructions:
  - A **dialogue line** = a line where the teacher or students speak actual words (quoted or in script format)
  - A **stage direction** = a summarized description of what happens, typically in `{braces}` or phrased as "Teacher does X" without quoting actual speech
  - A **specific example word** = a real word used in an activity (e.g., "zebra"), not a placeholder
  - A **specific child response** = names what children actually say (e.g., "children say /z/")
  - A **generic child response** = vague (e.g., "children respond", "children answer correctly")
- Evaluate Sections 1-4 only. Skip Section 5

### Report Format

```markdown
#### Script Specificity: 72.5%

| Section | Dialogue | Directions | Examples | Specific Resp. | Generic Resp. | Pacing? |
|---------|----------|------------|----------|----------------|---------------|---------|
| Review & Connect | 8 | 1 | 3 (zebra, tiger, apple) | 4 | 0 | + |
| Model, Explain & Engage | 15 | 2 | 2 (zebra, ball) | 6 | 1 | + |
| Guided Practice | 10 | 3 | 0 | 3 | 2 | + |
| Application | 6 | 4 | 2 (zebra, apple) | 2 | 1 | - |
| **Totals** | **39** | **10** | **7 words** | **15** | **4** | **3/4** |

Sub-metrics: Dialogue: 79.6% | Examples: 7 words | Responses: 78.9% | Pacing: 75.0%

**Judge Summary:** "..."
```

---

## Runner Integration

### New Eval Names

Add to `ALL_EVAL_NAMES`:

```
"think_aloud", "corrective_feedback", "post_response", "sound_comparison", "script_specificity"
```

### Registry Entries

Each new eval follows the same registry pattern. All 5 use the expert rubric criterion baked into their own rubric `.md` files (no separate form substitution needed):

| Eval Name | Label | Unit | Form |
|-----------|-------|------|------|
| `think_aloud` | ThinkAloud | items | `none` |
| `corrective_feedback` | Corrective | items | `none` |
| `post_response` | PostResp | responses | `none` |
| `sound_comparison` | SoundComp | items | `none` |
| `script_specificity` | Specificity | composite | `none` |

Unlike the existing evals that substitute `{form_d}` or `{form_b}` at runtime, these 5 evals have their rubric criteria and expert examples baked directly into their rubric `.md` files. The only substitution needed is `{lesson_output}`.

### CLI

The `--eval` flag should accept the new names:

```bash
# Run only the 5 new quality evals
--eval think_aloud corrective_feedback post_response sound_comparison script_specificity

# Run one new eval with one old eval
--eval think_aloud within

# Run all 11 (default)
(no --eval flag)
```

---

## Implementation Notes

- Use Context7 MCP tools to resolve library IDs and get latest docs for LangChain and Pydantic during implementation
- Follow the existing judge/compute/format function patterns exactly — read `run_scaffolding_evals.py` before implementing
- The `|` characters in judge reasoning must be escaped in markdown tables (existing pattern: `.replace("|", "\\|")`)
- Use `JUDGE_TIMEOUT=120` and `JUDGE_MAX_RETRIES=2` on all new judge calls (matching existing config)
- Each rubric `.md` file contains the full judge prompt with `{lesson_output}` placeholder. No additional form substitution needed — the rubric criteria and examples are baked into the prompt file itself
- The `script_specificity` eval has a composite score with weights. The compute function should return the composite as the main score but also expose sub-metrics in the detail output
- The judge functions for these 5 evals only need `lesson_output` and `model_key` as arguments (no form content), so the registry `"form"` field should be `"none"` and the runner should handle this case (pass `None` or skip the form argument)

---

## Verification

### Step 1: Run against expert fixture (should score high)

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend \
  python scripts/run_scaffolding_evals.py \
  --eval think_aloud corrective_feedback post_response sound_comparison script_specificity \
  --fixture expert_prek_letter_z_onlevel \
  --fixtures-dir tests/fixtures/handwriting_expert
```

**Expected:** The expert fixture should score well on these evals since it was written by a human expert following the rubric. If any eval scores below 70% on the expert fixture, the rubric prompt needs calibration — adjust the judge prompt until the expert fixture scores appropriately, then re-run.

### Step 2: Run against generated fixture (expect a gap)

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend \
  python scripts/run_scaffolding_evals.py \
  --eval think_aloud corrective_feedback post_response sound_comparison script_specificity \
  --fixture prek_letter_z_onlevel
```

**Expected:** The generated fixture should score noticeably lower than the expert on most evals, especially `script_specificity` and `think_aloud`. If the generated fixture scores within 10% of the expert, the eval is not discriminating well — tighten the rubric prompt criteria.

### Step 3: Run full suite on all fixtures

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend \
  python scripts/run_scaffolding_evals.py
```

**Expected:** All 11 evals run, report generates with all columns, no crashes. The 5 new eval columns should show meaningful score variance across fixtures.

### Calibration Loop

After each step, review the judge's structured output (the `evidence` fields) to verify the judge is correctly identifying the right parts of the lesson. If the judge is:
- **Missing things that are present** → the rubric prompt needs clearer definitions of what counts
- **Crediting things that aren't really there** → the rubric prompt needs stricter criteria
- **Scoring the expert low** → the checklist items may be too strict or not matching expert writing style

Iterate on the rubric `.md` files until the expert fixture scores ≥70% on all 5 evals and there is a visible gap between expert and generated scores.

Do not set pass/fail score thresholds. Review results manually after implementation.

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic models (8 new) | 🔲 Not started | `tests/evals/models.py` |
| Think-aloud rubric | 🔲 Not started | `tests/evals/rubrics/think_aloud.md` |
| Corrective feedback rubric | 🔲 Not started | `tests/evals/rubrics/corrective_feedback.md` |
| Post-response explanation rubric | 🔲 Not started | `tests/evals/rubrics/post_response_explanation.md` |
| Sound/letter comparison rubric | 🔲 Not started | `tests/evals/rubrics/sound_letter_comparison.md` |
| Script specificity rubric | 🔲 Not started | `tests/evals/rubrics/script_specificity.md` |
| Runner script integration (5 judge + 5 compute + 5 format + registry) | 🔲 Not started | `scripts/run_scaffolding_evals.py` |
| Criteria registry | 🔲 Not started | `app/langfuse/criteria.py` |
| Verification: expert fixture | 🔲 Not started | Target: ≥70% on all 5 evals |
| Verification: expert vs generated gap | 🔲 Not started | Target: visible score gap |
| Verification: full suite (all 11) | 🔲 Not started | No crashes, all columns populated |

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `tests/evals/rubrics/think_aloud.md` | Judge prompt for think-aloud eval |
| `tests/evals/rubrics/corrective_feedback.md` | Judge prompt for corrective feedback eval |
| `tests/evals/rubrics/post_response_explanation.md` | Judge prompt for post-response explanation eval |
| `tests/evals/rubrics/sound_letter_comparison.md` | Judge prompt for sound/letter comparison eval |
| `tests/evals/rubrics/script_specificity.md` | Judge prompt for script specificity eval |

### Modified Files

| File | Changes |
|------|---------|
| `tests/evals/models.py` | Add 8 new models: `ThinkAloudInstance`, `ThinkAloudOutput`, `CorrectiveFeedbackBlock`, `CorrectiveFeedbackOutput`, `StudentResponse`, `ActivityResponses`, `PostResponseOutput`, `ComparisonBlock`, `SoundLetterComparisonOutput`, `SectionSpecificity`, `ScriptSpecificityOutput` |
| `scripts/run_scaffolding_evals.py` | Add 5 judge + 5 compute + 5 format functions, extend `EVAL_REGISTRY` with 5 entries, extend `ALL_EVAL_NAMES`, handle `"none"` form type |
| `app/langfuse/criteria.py` | Add 5 `llm-judge` entries to `CRITERIA_REGISTRY` |

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-18 | Initial draft — 5 new instructional quality evals |
| 0.2 | 2026-02-19 | Fix scoring: PostResp min response floor of 3; Specificity per-section volume floor of 10 dialogue lines |
