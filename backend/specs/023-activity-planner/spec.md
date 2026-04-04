# Spec 023: Activity Planner — Smart Activity Selection for Lesson Generator

## Status: Planned

## Problem

The handwriting generator currently dumps ALL reference materials (~16.6K tokens) into one system prompt and asks the LLM to select appropriate activities from Form D based on student level tags (low/middle/high). This causes:

1. **Wrong activity selection** — The LLM picks activities from the wrong level, mixes up activity names, or selects activities inappropriate for the grade (14 open bugs from Dr. Farrow's March 9 feedback).
2. **No previously-learned-skills awareness** — The generator uses untaught sounds in examples and can't judge readiness for advanced activities.
3. **No skill focus** — No way to target a specific skill (isolating sounds, blending, letter formation, spelling).
4. **Bloated prompt** — Forms F (52 letters) and G (37 sounds) are loaded in full when only 1-2 entries are needed per lesson.
5. **Form D is outdated** — Dr. Farrow's new Activity Framework (85KB) supersedes Form D with richer cognitive rationale, but it's too large to dump into the prompt.

## Solution

Replace the generator's internal activity selection with a **two-stage pipeline**:

1. **Activity Planner node** — An LLM agent reads the activity index (~2.3K tokens), selects 4-5 activities by slug, and returns a structured `ActivityPlan`.
2. **Generator node** — Receives the plan, loads only the selected activity descriptions + filtered Form F/G entries, and generates the lesson with focused context (~6.4K tokens).

Total combined tokens: ~9.1K (down from 16.6K current, and far below the 27K it would be if we naively added the framework).

## Architecture

### New graph flow

```
param_agent (5 questions)
     │
     ▼
activity_planner ◄── NEW: selects 4-5 activities + standards
     │
     ▼
handwriting_generator ◄── receives plan + filtered materials
     │
     ▼
image_assembly → image_director → END
```

Modifications loop back to `handwriting_generator` directly (planner runs once per lesson).

### New intake parameters

Two new fields added to `HandwritingParams`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `previously_learned` | `list[str]` | No | `[]` | Sounds/letters already taught (e.g., `["m", "a", "s", "t"]`) |
| `skill_focus` | `SkillFocus` | No | `"isolating_sounds"` | One of: `isolating_sounds`, `blending`, `letter_formation`, `spelling` |

The param agent asks these alongside the existing 3 questions (grade, letter, student_level).

### New files

| File | Purpose |
|------|---------|
| `prompt/reference_materials/handwriting/activity-framework.md` | Dr. Farrow's activity descriptions with `### [slug] Name` headings |
| `prompt/reference_materials/handwriting/activity-index.yaml` | Structured index: 30 activities with grade-keyed levels, prerequisites, skill focus |
| `app/graph/utils/extractors.py` | Regex extraction functions for activities, Form F, Form G, standards |
| `app/graph/agents/activity_planner.py` | Planner agent + `submit_activity_plan` tool |
| `app/graph/nodes/activity_planner.py` | Planner graph node |
| `tests/unit/test_extractors.py` | Unit tests for regex extraction (already committed) |
| `tests/unit/test_activity_index.py` | Unit tests for index structure (already committed) |
| `tests/unit/test_planner_validation.py` | Unit tests for plan validation (already committed) |
| `tests/unit/test_prompt_assembly.py` | Unit tests for prompt filtering (already committed, skipped until implementation) |

### Files modified

| File | Changes |
|------|---------|
| `app/graph/state.py` | Add `previously_learned`, `skill_focus` to `HandwritingParams`; add `ActivityPlan` TypedDict; add `activity_plan` to `GraphState` |
| `app/graph/agents/param.py` | Add 2 new fields to `SubmitHandwritingParams` schema; update prompt |
| `app/graph/agents/handwriting_generator.py` | Remove Form D, F (full), G (full), H from `COMMON_FORM_FILES`; add `activity_plan` param to prompt builder; rewrite `get_handwriting_generator_prompt()` to use filtered materials |
| `app/graph/graph.py` | Add `activity_planner_node`; update `route_after_param_agent` to route to planner; add edge from planner to generator; update `extract_handwriting_params` for new fields |

### Files removed from generator prompt

| File | Current | New |
|------|---------|-----|
| `form-d-scaffolded-activities.md` | Full (59 lines) | **Removed** — replaced by activity plan |
| `form-f-verbal-cues.md` | Full (61 lines) | 2 lines (target letter only, via regex) |
| `form-g-phoneme-gestures.md` | Full (76 lines) | 1-2 rows (target sound only, via regex) |
| `form-h-modifications.md` | Always loaded (53 lines) | Lazy-loaded on modification requests only |
| `activity-framework.md` | N/A (not loaded) | 4-5 activity descriptions extracted by slug (~50-75 lines) |

---

## Implementation Details

### 1. Extraction functions (`app/graph/utils/extractors.py`)

Four regex functions, each under 10 lines:

```python
def extract_activity(framework: str, slug: str) -> str
    # Pattern: ^### \[{slug}\] .+?\n(.*?)(?=^### \[|^## |\Z)

def extract_verbal_cues(form_f: str, letter: str) -> str
    # Pattern: ^[{UPPER}{lower}]\s*–\s*.+$

def extract_gesture(form_g: str, letter: str) -> str
    # Pattern: ^\|[^|]*/{sound}/[^|]*\|.+$
    # Uses LETTER_TO_SOUNDS mapping (vowels return both short + long)

def extract_grade_standards(standards: str, grade_header: str) -> str
    # Pattern: ^##\s+{header}\b.*?\n(.*?)(?=^##\s|\Z)
```

Letter-to-sounds mapping for Form G:
- Consonants: 1:1 (b→/b/, d→/d/, etc.)
- Vowels: short + long (a→[/a/, /ā/], e→[/e/, /ē/], etc.)
- Edge cases: c→/k/, g→/g/, q→/qu/, x→/x/

### 2. Activity index (`activity-index.yaml`)

30 activities across 4 sections. Each activity has:

```yaml
- name: Sound Spark                              # display name (can change)
  rank: 3                                        # difficulty order within section
  summary: "Teacher points to card, children pronounce."
  skill_focus: [isolating_sounds]
  prerequisites: "~90% accuracy on Tap that Sound"
  by_grade:                                      # grade-keyed levels
    PreK: { levels: [on-level, advanced] }
    K:    { levels: [on-level, advanced] }
    1st:  { levels: [struggling, on-level, advanced] }
```

The `by_grade` structure captures that the same activity can be `[advanced]` for K but `[struggling, on-level, advanced]` for 1st grade — flat level arrays can't express this.

Section counts: Review (6), Sound Target Focus (7), Handwriting Focus (10), Spelling Focus (7).

### 3. Activity framework (`activity-framework.md`)

Reformatted with slug headings for regex extraction:

```markdown
## Review (5 min)

### [sound_spark] Sound Spark

The teacher points to a letter-sound card (e.g., m)...
[full prose from Dr. Farrow — cognitive rationale, readiness signals, etc.]

### [sort_the_sound] Sort the Sound
...
```

30 activities with `### [slug] Display Name` format. The slug is the stable machine ID; the display name can change.

### 4. Planner agent (`app/graph/agents/activity_planner.py`)

Receives:
- 5 intake parameters from `HandwritingParams`
- The full activity index YAML (~2.3K tokens)

Returns structured output via Pydantic tool:

```python
class SubmitActivityPlan(BaseModel):
    review: str              # slug from index
    sound_target: str        # slug from index
    handwriting: str         # slug from index
    handwriting_chain: str | None  # optional rehearsal→writing chain
    spelling: str            # slug from index
    standards: list[str]     # standard codes (e.g., ["K.F.PA.6.a", ...])
```

The planner selects ONE activity per section based on:
- Grade compatibility (non-null in `by_grade`)
- Level compatibility (student_level in `by_grade[grade].levels`)
- Skill focus alignment (activity's `skill_focus` matches intake)
- Prerequisites met (based on `previously_learned`)
- Difficulty rank (appropriate for readiness level)

### 5. Planner output validation

After the planner returns an `ActivityPlan`, Python validates:
1. All slugs exist in the index
2. Each slug belongs to the correct section
3. No slug is `null` for the given grade
4. Each slug's grade config includes the student level
5. Standards cover all required domains (PA, Phonics, Encoding, Handwriting for K/1st)

If validation fails, retry the planner with error feedback (max 2 retries).

### 6. Generator prompt changes

**Rule 3 (Activity Selection)** changes from:
> Based on student level, use LOW/MIDDLE/HIGH activities from Form D

To:
> Follow the Activity Plan below. Each section has a pre-selected activity. Name every activity exactly as shown.

**Rule 2 (Verbal Cues)** changes from:
> Look up the correct verbal cues for letter "{letter}" in Form F

To:
> The verbal cues for letter "{letter}" are provided below. Use them EXACTLY.

**Rule 12 (Prior Practice)** changes from:
> Do not use sounds that have not been directly taught

To:
> The student has learned these sounds: {previously_learned}. Use ONLY these + the target sound.

New prompt template sections:

```
## Activity Plan
{activity_plan_with_descriptions}

## Verbal Cues
{filtered_form_f}

## Phoneme Gesture
{filtered_form_g}

## Standards
{pre_selected_standards}

## Reference Materials
{forms_a_b_c_e_only}
```

### 7. Modification loop

The planner runs **once** per lesson. When the teacher requests modifications:
- Entry router detects `handwriting_params` set → routes to `handwriting_generator` (skips planner)
- Form H is lazy-loaded into the generator context on re-entry
- The generator handles modifications with the existing activity plan
- If the teacher wants fundamentally different activities, they start a new conversation

### 8. `previously_learned` normalization

The param agent collects this as free text from the teacher. Normalization:
- Extract individual letters/sounds
- Lowercase, deduplicate
- Store as `list[str]` (e.g., `["m", "a", "s", "t"]`)
- Empty list = first lesson ever → planner picks entry-level activities

---

## Token Budget

| Component | Current | New |
|-----------|---------|-----|
| Generator prompt | ~10,943 | ~6,430 |
| Planner prompt | — | ~2,712 |
| **Combined** | **~10,943** | **~9,142** |
| **Change** | | **-16%** |

Breakdown of generator savings:
- Form D removed: -1,921 tokens
- Form F filtered (52→2 lines): -648 tokens
- Form G filtered (37→1-2 rows): -868 tokens
- Form H removed from initial: -800 tokens
- Activity descriptions added: +1,105 tokens (4-5 activities from framework)
- New parameters + plan: +263 tokens

---

## Testing Strategy

### Pre-committed tests (define the contract)

| Test file | Tests | LLM? |
|-----------|-------|------|
| `tests/unit/test_extractors.py` | 30+ tests: regex extraction from framework, Form F, Form G, standards | No |
| `tests/unit/test_activity_index.py` | 20+ tests: YAML structure, slugs, by_grade, section counts, cross-reference | No |
| `tests/unit/test_planner_validation.py` | 15+ tests: valid/invalid plans, grade/level constraints, section membership | No |
| `tests/unit/test_prompt_assembly.py` | 15+ tests: filtering, inclusion/exclusion of materials (skipped until impl) | No |

### Post-implementation tests

| Test | What it validates |
|------|-------------------|
| Planner eval | LLM picks valid, appropriate activities for various grade/level/focus combos |
| Generator eval (existing) | Lessons still pass structure, verbatim, verbal cue checks with new prompt |
| Scaffolding eval (existing) | Activity sequencing quality maintained or improved |

### Test change policy

The implementation agent may modify test assertions ONLY if a test has a bug (wrong expected value). It may NOT weaken tests (remove assertions, loosen checks, skip tests). If it believes a test expectation is wrong, it must leave a comment explaining why and flag it for review.

---

## Edge Cases

### Grade + skill_focus conflicts
- **PreK + blending**: Limited options (Chop/Switch-a-Roo null for PreK). Planner falls back to next-best skill focus.
- **1st + letter_formation**: Most rehearsal activities null. Planner selects writing-based activities (Start Dot & Say, Write the Sound Challenge, Cover & Try).

### Form G vowel sounds
Vowels return both short AND long sound rows (e.g., letter "A" → `/a/` + `/ā/`). The `LETTER_TO_SOUNDS` mapping handles this.

### Duplicate "Write the Sound"
Disambiguated by slug: `write_the_sound_review` (Review section) vs `write_the_sound_spelling` (Spelling section). Framework headings use `### [slug]` format so regex extraction is unambiguous.

### Handwriting chain
The planner may return `handwriting_chain` (optional second activity for Guided Practice). The generator prompt must explain the rehearsal→writing progression. If chain is null, generator uses the single `handwriting` activity.

### Empty `previously_learned`
First lesson ever. Planner picks entry-level activities: Sound Echo (review), Sound Check (model), Finger Run or SkyWrite (handwriting), Trace the Sound (spelling).

---

## Implementation Order

1. `app/graph/utils/extractors.py` — 4 regex functions + `LETTER_TO_SOUNDS` mapping
2. `app/graph/state.py` — Add `SkillFocus`, update `HandwritingParams`, add `ActivityPlan`, update `GraphState`
3. `app/graph/agents/param.py` — Add 2 fields to `SubmitHandwritingParams`, update prompt
4. `app/graph/agents/activity_planner.py` — Planner agent with `submit_activity_plan` tool
5. `app/graph/graph.py` — Add planner node, update routing, add validation
6. `app/graph/agents/handwriting_generator.py` — Rewrite prompt assembly with filtered materials
7. `tests/unit/test_prompt_assembly.py` — Remove skip markers, verify against real implementation
8. Run existing evals to verify no regression

---

## Standards Pipeline (addendum, 2026-04-03)

The initial implementation left standards selection incomplete — the planner hallucinated codes because it had no reference, and the generator independently selected its own from a full dump. This addendum completes the dispatcher pattern for standards.

### Problem

Three-part gap discovered during eval:

1. **Planner has no standards reference** — prompt tells it to "Select grade-appropriate codes" but provides no valid code list. Result: fabricated codes (`K.F.ASR.1`, `K.F.PGR.3`, `K.F.ENC.1`, `K.F.HWR.1`).
2. **No standards validation** — `activity_planner_node` validates slugs, grade, and level but not standards codes. Fabricated codes pass through unchecked.
3. **Generator ignores planner's standards** — Rule 5 says "Select... Include at least 4 standards" and receives the full grade standards section (~300-500 tokens). The planner's selections are comma-joined in the activity plan section but the generator picks its own.

### Solution

Apply the same dispatcher pattern used for activities: reference → planner selects → validator checks → generator receives only selected items.

### New function: `extract_standard()` in `extractors.py`

```python
def extract_standard(standards_text: str, code: str) -> str:
    """Extract a single standard code + description from the reference file."""
    # Match table row: | CODE | description |
    # Whole-file search — codes are unique across grades (CLL* vs K.F.* vs 1.F.*)
    # Must not partial-match: K.F.PA.6 must NOT match K.F.PA.6.a
```

Returns `"CODE — description"` or `""`.

### New function: `validate_plan_standards()` in `activity_planner.py` (node)

Validates the planner's selected standards codes:

1. **Code existence** — each code must exist in the reference file (via `extract_standard`)
2. **Grade system** — each code must use the correct prefix:
   - PreK: must start with `CLL`
   - K: must start with `K.F.`
   - 1st: must start with `1.F.`
3. **Category coverage** (K and 1st only) — must have at least one standard from each of:
   - Phonemic Awareness (PA)
   - Phoneme-Grapheme Correspondence (P.1)
   - Encoding (P.3)
   - Handwriting (H)
4. **Minimum count** — PreK: 1-3 codes; K/1st: at least 4
5. **Non-empty** — `standards=[]` is always an error

Wired into the existing retry loop alongside `validate_plan_slugs`, `validate_plan_grade`, `validate_plan_level`.

### Planner prompt changes

Add grade-filtered standards reference to the planner prompt (~300-500 tokens):

- Load `handwriting-spelling-standards.md`
- Call `extract_grade_standards()` with the grade header (reuse existing `GRADE_TO_STANDARDS_HEADER` mapping)
- Insert as `{grade_standards}` in the prompt template
- Update the Standards instruction section to say "Select from the reference below" instead of just listing code formats

### Generator prompt changes

1. **Remove `{grade_standards}` section** — the full "Grade-Specific Standards Reference" dump is no longer needed
2. **Rewrite Rule 5** — from "Select standards" to "Use the pre-selected standards from the Activity Plan exactly. Do NOT select new ones."
3. **Update "Your Task" header** — add `previously_learned` and `skill_focus` to the parameter list
4. **Enhance `build_activity_plan_section()`** — resolve standard codes to `"code — description"` via `extract_standard()` instead of comma-joining bare codes

### Files modified

| File | Changes |
|------|---------|
| `app/graph/utils/extractors.py` | Add `extract_standard()` |
| `app/graph/nodes/activity_planner.py` | Add `validate_plan_standards()`, wire into retry loop, load standards file |
| `app/graph/agents/activity_planner.py` | Add grade-filtered standards to planner prompt |
| `app/graph/agents/handwriting_generator.py` | Remove `{grade_standards}`, rewrite Rule 5, update task header, enhance `build_activity_plan_section()` |

### Unit tests (pre-committed)

| Test file | Class | Tests |
|-----------|-------|-------|
| `test_extractors.py` | `TestExtractStandard` | 13 tests: code extraction, fabricated codes, partial match, cross-grade, completeness (all 34 codes) |
| `test_planner_validation.py` | `TestValidStandards` | 4 tests: valid plans for K, PreK, 1st, fewer PreK codes |
| `test_planner_validation.py` | `TestInvalidStandards` | 10 tests: fabricated codes, wrong grade system, missing categories (PA, P.1, P.3, H), empty list, 1st grade category check |
| `test_prompt_assembly.py` | `TestStandardsNotInGenerator` | 5 tests: no full dump, no "Select" instruction, plan standards + descriptions included |
| `test_prompt_assembly.py` | `TestPromptParameters` | 2 tests: `previously_learned` and `skill_focus` in task header |

### Implementation order

1. `extract_standard()` in `extractors.py`
2. `validate_plan_standards()` in `activity_planner.py` (node) + wire into retry loop
3. Planner prompt: add grade-filtered standards reference
4. Generator prompt: remove standards dump, rewrite Rule 5, update task header
5. `build_activity_plan_section()`: resolve codes to descriptions
6. Run unit tests
7. Regenerate K fixture, re-run evals

---

## Acceptance Criteria

- [ ] All pre-committed unit tests pass (`test_extractors`, `test_activity_index`, `test_planner_validation`, `test_prompt_assembly`)
- [ ] Planner returns valid `ActivityPlan` for all 9 grade×level combinations
- [ ] Generator prompt contains only target letter cues (Form F), target sound gesture (Form G), and selected activity descriptions
- [ ] Generator prompt does NOT contain Form D, full Form F, full Form G, or Form H (on initial generation)
- [ ] Generator prompt does NOT contain the full grade standards reference
- [ ] Standards in the generated lesson are real codes from the reference file
- [ ] Existing handwriting generator evals pass at current or better scores
- [ ] Existing scaffolding evals pass at current or better scores
