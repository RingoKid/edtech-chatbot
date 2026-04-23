# LC Prototype Review Tracker

Long-form review and analysis notes for the LC prototype. Kept separate from `TODO-LC.md` so that file stays focused on actionable tasks.

Two review cycles captured here, newest first:

1. **Cycle 4** (2026-04-23) — Dr. Farrow's review of three K lessons with varied parameters
2. **Cycle 3** (2026-04-19 → ongoing) — Section-by-section walkthrough of the reproduction test

---

## Cycle 4 — Dr. Farrow review of varied-parameter K lessons (2026-04-23)

### Scope

Three K lessons generated on 2026-04-20 by `backend/scripts/prototype_lc_generator.py`, each varying one axis off the baseline (Informational + Be-verbs + on-target):

| # | Lesson | Dropbox filename | Status |
|---|---|---|---|
| 1 | K Informational — Plants / One-Word Adverbs / More Support | `AI Sample - K Informational - Plants (One-Word Adverbs, More Support).docx` | ✅ reviewed 2026-04-23 (19 comments) |
| 2 | K Narrative — Fire Station / Prepositional Phrases / On-target | `AI Sample - K Narrative - Fire Station (Prepositional Phrases).docx` | ⏳ pending |
| 3 | K Opinion — Favorite Season / Adjectives / On-target | `AI Sample - K Opinion - Favorite Season (Adjectives).docx` | ⏳ pending |

Dropbox folder: `~/Library/CloudStorage/Dropbox/Vocabulary & Syntax (language construction) AI codes/AI Generated Lesson Samples/`

Raw comments extracted to: `backend/resources/expert-feedback/dr-farrow-feedback-lc-plants-k-adverbs.md` (committed `26094d7`)

### Action items from LP 1 (19 comments clustered into 15 tasks)

#### A. Prompt rule changes — generator is producing structurally wrong output

- [ ] **A.1 Non-example contrast rule for adverbs** — when `sentence_structure_focus = one-word adverbs`, non-examples MUST be adjective sentences, not be-verb sentences. Example: "The happy boy ran" (adj) vs "The boy ran fast" (adv). Rationale: be-verb adverbs in K are often phrases, which introduces cognitive load before kids can distinguish adjectives from adverbs. *Generalizes: each target structure needs an explicit "right-level contrast" in the rule set — we're currently leaving contrast choice to the model.* (comments on paras 84, 91, 167)
- [ ] **A.2 Guided Practice = exactly 1 activity** — current Rule 2 says "1–2 activities per subsection"; Dr. Farrow says Guided Practice is ONE activity with teacher scaffolding. Tighten rule to cap Guided Practice at 1. (para 104)
- [ ] **A.3 Example Bank placement** — must come immediately after the activity script it supports, not floating between activities. Update the subsection ordering rules. (para 60)
- [ ] **A.4 Act-It-Out-Quick positioning** — belongs at the top of Review & Connect (with vocab review) or at the end as a connector. Do NOT insert it between Spotlight Sentence and Example Bank. (para 60)
- [ ] **A.5 Spotlight Sentence uses same-verb type only** — when priming kids on action-verb identification, all Spotlight Sentence examples should be action-verb sentences. No be-verb mixing (generator included "The sprout is small" which broke the priming). (para 53)
- [ ] **A.6 Wrap-Up comparison target → adjectives** — "how are adverbs different from **adjectives**", not be-verbs. Matches A.1. (para 167)
- [ ] **A.7 Teacher questions must redirect to the verb** — when asking "is 'today' how/when/where?", reframe as "is 'today' showing us **how** it sprouted, **where** it sprouted, or **when** it sprouted?" — anchoring every answer to the action. (paras 172 ×2)

#### B. Teacher script vs. meta-instruction separation

- [ ] **B.8 New component marker for teacher notes** — lines like "Worked example number one. Listen: 'The sprout grows slowly.' The action verb is 'grows.'" are *cues to the teacher*, not what the teacher says aloud. Need a marker like `📘 **Teacher Note:**` (or bracketed block) distinct from `🗣️ **Teacher:**` (child-facing dialogue). Dr. Farrow suggested color or brackets. (paras 74, 84)

#### C. Activity content quality

- [ ] **C.9 Build-A-Sentence needs worksheet structure** — subject pictures, space for action verb, space for adverb. Each row prompts the adverb question ("how?", "when?", "where?"). Encourage invented spelling. Current Form K description is too loose. (paras 114, 135)
- [ ] **C.10 Sentence Hunt replaces Same-or-Different** — display sentences, kids pick the one with the one-word adverb. Contrast sentence is always a one-word adjective sentence. (para 91)
- [ ] **C.11 Picture Sentence replaces Stretchy Sentence** — flow: draw → orally rehearse → write with invented spelling → circle the adverb. Teacher walks through: picture → sentence → label noun/verb → pick adverb → write. Struggling kids get told *what* to draw. (para 141 ×2)
- [ ] **C.12 Realistic corrective feedback examples** — "The bloom pink" isn't a natural K error. Realistic errors: be-verb substitution ("The flowers are beautiful") or adverb-phrase substitution ("in the morning" instead of "today"). Script should affirm adverb-phrase as "something hard we'll talk about later" rather than correct it as wrong. (paras 132, 153)

#### D. Rendering (pandoc/markdown convention)

- [ ] **D.13 Box Corrective Feedback blocks** — visually box them in the docx output so they're easier to spot. Options: markdown blockquote + bold label, or a custom pandoc reference docx with a "Corrective Feedback" paragraph style. (paras 97, 101)
- [ ] **D.14 Box Example Banks** — same rationale as D.13. (para 101)

#### E. Objectives

- [ ] **E.15 Add "expand sentences using adverbs" objective** — or rephrase an existing objective to reflect this. (para 13)

### Holding / pending

- [ ] **Form K updates** — Dr. Farrow modified `FORM K_ Scaffolded Activities for Vocabulary & Sentence Structure .docx` on 2026-04-23 14:35. She noted she'll likely update it again as she reviews LP 2 + 3. **Hold** re-ingestion of Form K into `form-k-scaffolded-activities.md` until all three LPs are reviewed — otherwise we re-do the work.
- [ ] **LP 2 review (Fire Station / Prepositional Phrases)** — awaiting Dr. Farrow.
- [ ] **LP 3 review (Favorite Season / Adjectives)** — awaiting Dr. Farrow.

### Next step

Pick up in a new chat to start cutting the prompt rule changes. Start with the quick-win category A items (A.2, A.3, A.6 are small) before the bigger ones (A.1, B.8, the C.* activity rewrites which need Form K coordination).

---

## Cycle 3 — Section-by-section walkthrough (2026-04-19 → ongoing)

### Why we're doing this

Comparing the v3 generated lesson plan against the reference example, section by section, to:

1. **Understand each section** — what it's doing pedagogically and how it's doing it
2. **Map output to prompt** — for each section, pinpoint the exact system-prompt lines/rules that drive its content, structure, and styling
3. **Collect prompt-improvement TODOs** — every divergence that isn't cosmetic feeds into a punch list for later prompt edits
4. **Decide per-section whether to add an eval** — if a behavior is load-bearing AND testable from output alone, capture it as an eval candidate
5. **Build a complete mental model** of the prompt → output relationship so future prompt edits are informed, not random
6. **Evaluate whether this walkthrough methodology itself should become a reusable sub-skill** (e.g. `/dev lc-compare`) once we see how it plays out across all 10 sections

This is **not** a verbatim-match exercise. v3 generated output and reference are both legitimate lessons — we're looking at how well the prompt encodes the *shape* of a good lesson, not whether the AI produced identical text.

### Files in play (cycle 3)

| Role | Path |
|---|---|
| System prompt source | `backend/scripts/prototype_lc_generator.py` (template lines 75–167; rules 1–13 at lines 117–151) |
| Generated output (v3) | `backend/scripts/prototype-lc-outputs/lc_lesson_K_2026-04-20_025048.md` (385 lines) |
| Reference (comparison target) | `backend/prompt/reference_materials/language_construction/prompt-ready/lesson-plan-k-example.md` (385 lines) |
| Standards fact-check source | `backend/prompt/reference_materials/language-construction-standards.md` |
| Other reference materials injected | Form I (lesson structure), Form M (genre), Form R (sentence structure), Form K (scaffolded activities), Form E (best practices) — all under `backend/prompt/reference_materials/language_construction/prompt-ready/` |

**Cycle 3 inputs** (in `INPUTS` dict of `prototype_lc_generator.py`): grade K / informational / weather & temperature / vocabulary [weather, temperature, thermometer, chilly, freezing] / sentence structure "Be-verbs" / previously learned action verbs + -y adjective rule / ability level "on target". **Identical to the reference example inputs** — any divergence in output reflects prompt design, not input drift.

### How to run a section comparison (resumable method)

For each section below, follow these steps:

1. **Pull the section from all three sources**
   - Read the section from v3 output (use `Read` with `offset`/`limit`)
   - Read the same section from the reference
   - Locate the prompt lines that govern the section in `prototype_lc_generator.py`:
     - Output structure clauses: lines 91–105 (sections A/B/C/D, subsection order)
     - Component markers: lines 107–114 (emoji markers and when to use them)
     - Rules 1–13: lines 117–151 (mapped below)

2. **Describe what the section is doing** — one sentence on pedagogical purpose (from Form I for D subsections).

3. **Map prompt-to-output**
   - Which template line numbers specify the structure?
   - Which numbered rules govern the content? (e.g. Rule 6 = worked + non-examples, Rule 8 = corrective feedback, Rule 2 = Form K activity names)
   - Which reference material is being used as ground truth? (Form I for explanations, Form K for activities, Form R for sentence structures, Form M for genre, standards file for codes)

4. **Compare verdict-style**
   - ✅ **Matching** — same structure, content, style
   - ⚠️ **Cosmetic drift** — different styling but pedagogically equivalent (e.g. bold vs plain labels, bullet vs paragraph)
   - 🔴 **Real gap** — missing rule application, content fabrication, or pedagogical regression

5. **Collect TODOs** — any actionable prompt improvement goes into "TODO list for prompt updates" below, tagged with the section that surfaced it.

6. **Eval decision** — apply the criteria below. If yes, add to "Eval candidates."

### Rule-to-section cheat sheet

| Section | Primary prompt drivers |
|---|---|
| Title + Input | lines 104–105 (H2 title + byline + Input list format) |
| A. Standards | line 94 + Rule 10 (line 144) + standards reference block |
| B. Objectives | line 95 ("listed in order of difficulty") |
| C. Materials | line 96 ("concrete list") |
| D.1 Review & Connect | Rule 1 (Form I purpose quote), Rule 9 (bridge from previously learned), Rule 11 (turn-taking), Rule 2 (Form K activity names), Rule 5 (example bank) |
| D.2 Model, Explain & Engage | Rule 1, Rule 6 (2 worked + 2 non-examples), Rule 7 (genre integration), Rule 8 (corrective feedback), Rule 2, Rule 5 |
| D.3 Guided Practice | Rule 1, Rule 2, Rule 3 (activity-level matching), Rule 4 (verbatim script), Rule 5, Rule 8, Rule 11 |
| D.4 Application | Rule 1, Rule 3 (high-level activity for on-target), Rule 5, Rule 8 |
| D.5 Wrap-Up | Rule 1, Rule 11, Rule 12 (warmth, not clinical) |
| Adaptation footer | Rule 13 (verbatim closing line) |

### Eval decision criteria

Add to "Eval candidates" if **all three** hold:

- **Output-testable** — behavior can be verified from the markdown alone (no graph state, no human judgment)
- **Class of error, not instance** — the test catches a family of regressions, not just today's bug
- **Load-bearing** — silent failure would ship a materially worse lesson to teachers

Examples that qualify: "every standards code exists in the standards file," "every activity name matches a heading in Form K," "every section opens with 💡 + verbatim Form I quote."

Examples that don't qualify: "bolding on Input labels" (cosmetic), "title uses em-dash" (stylistic).

### Section checklist

- [x] 0. Title + Input block — done 2026-04-19
- [x] A. Standards — done 2026-04-19 (surfaced K.L.GC.2.c miscoding, fixed)
- [x] B. Objectives — done 2026-04-20 (objectives match D activities; surfaced 3 cross-section TODOs)
- [x] C. Materials — done 2026-04-20 (no prompt rule beyond "concrete list"; tooling idea to make C a downstream pass)
- [ ] D.1 Review & Connect
- [ ] D.2 Model, Explain & Engage
- [ ] D.3 Guided Practice
- [ ] D.4 Application
- [ ] D.5 Wrap-Up
- [ ] Adaptation footer

### Findings log

#### Section 0 — Title + Input block ✅ (2026-04-19)

**Prompt driver:** lines 104–105 of template.

**What matched:** Grade, genre, unit focus, vocabulary (5 words), sentence structure focus ("Be-verbs"), previously learned phrasing, ability level — all input fields echoed correctly.

**Cosmetic drift:**
- v3 expands structure verbatim into title (`Be-verbs (Weather and temperature)`); reference condenses (`Be-Verbs (Weather/Temperature)`). Caused by template literal `## Lesson Plan {grade}: Sentence Structure — {sentence_structure_focus} ({unit_focus})`.
- v3 bolds every Input label (`**Grade:**`); reference uses plain labels. Caused by the prompt template itself bolding the field names at lines 83–89 — model mirrors the prompt's own styling.
- v3 orders Input list Grade → Genre → Unit Focus → ... (matches template order); reference leads with Unit focus.
- v3 ability level is lowercase "on target"; reference is "On target." (v3 echoed `INPUTS` dict value verbatim).

**Real gaps:** none.

**TODOs surfaced:** none (all cosmetic).

**Eval candidate:** maybe — "every lesson starts with `## Lesson Plan {grade}:` H2 and includes a labeled `**Input:**` block." Low ROI; format is enforced by the prompt's explicit template so regression is unlikely unless the template itself changes.

#### Section A — Standards ✅ (2026-04-19)

**Prompt drivers:** line 94 (structure clause) + Rule 10 (line 144, priority order + "do not fabricate") + standards reference block injected at top of reference materials.

**v3 produced:**
```
- K.L.GC.2.a — Recognize that conventional sentences always include a subject and a predicate.
- K.L.V.1.b — Use grade-level general, academic, and specialized vocabulary...
- K.P.AC.2.c — Make decisions about sentence structure and syntax...
```

**Reference produced (post-fix):**
```
K.P.AC.2.c — Make decisions about sentence structure and syntax...
K.L.GC.2.a — Recognize that conventional sentences always include a subject and a predicate.
K.L.GC.2.b — With adult support, use simple sentences to express complete thoughts in written texts.
```

**What matched / exceeded:**
- v3 selected 3 codes within the prompt's 1–3 range ✅
- All 3 codes exist verbatim in `language-construction-standards.md` ✅
- v3 followed Rule 10's priority order (GC → V → AC); **reference violates it** (AC first). AI out-aligned the human reference on stated priority.

**What we caught:** reference's original `K.L.GC.2.c` description was miscoded — it belonged to `K.L.GC.2.b`. Fixed in both copies this session.

**Cosmetic drift:**
- v3 uses bulleted list with `**bold code**`; reference uses plain-paragraph format. Driven by the prompt template's bullet styling, not by a rule.

**Real gaps:** none in v3. The miscoding was in the human-authored reference.

**TODOs surfaced:**
- [ ] Decide whether Rule 10's stated priority (GC → V → AC) should stand, given the reference violates it. Check with Dr. Farrow if the AC-first ordering in reference was intentional. (from Section A)

**Eval candidate: YES — HIGH VALUE**
- [ ] **Standards fidelity eval** — for any generated LC lesson, assert (1) every code in `### A. Standards` exists in `language-construction-standards.md`, (2) the description matches the standards file verbatim, (3) count is within 1–3. Would catch hallucinations AND reference miscodings. Tentative file: `backend/tests/evals/lc/test_standards_fidelity.py`.

#### Section B — Objectives ✅ (2026-04-20)

**Prompt driver:** template line 95 ("listed in order of difficulty"). Form I adds no objectives-specific guidance.

**Verdict:** ✅ Matching. Both lessons list 4 objectives, ordered by difficulty, and a standalone audit confirmed every objective is delivered by activities in Section D. v3 is more pedagogically explicit (names modality "orally say", ties obj 1 to previously-learned vocab); reference is terser with headline-style verbs.

**Cosmetic drift:** v3 ends bullets with periods, reference doesn't.

**Real gaps in B itself:** none. But the cross-section audit surfaced 3 issues affecting D — see TODOs below.

**Eval candidate: YES — MEDIUM VALUE**
- [ ] **Objective coverage eval** — every bullet in `### B. Objectives` has ≥1 matching activity in Section D. Testable via semantic mapping. Would catch orphaned objectives and skipped activities.

#### Section C — Materials ⚠️ (2026-04-20)

**Prompt driver:** template line 98 only ("Concrete list of what the teacher will need."). No Rule 1–13 governs C.

**Verdict:** ⚠️ Cosmetic drift + one structural gap. v3's list (10 items) is more granular and activity-aware than the reference's (6 items) — v3 explicitly supports be-verb work with `is/am/are` word cards, sentence-strip space, and a thumbs routine; reference skips these. Both satisfy line 98's "concrete list." Neither enforces Materials↔activities coherence.

**Cosmetic drift:** v3 has one internal redundancy (`hot/warm/cool` listed twice under different labels). Reference's "Noun pictures" pulls in non-vocab items (wind/storm/ice) while v3 stays tighter to `{vocabulary}`.

**Real gap:** Materials list isn't tied to activities in D. v3 over-lists; reference under-lists (missing be-verb word cards). Silent failure in both directions — the teacher can't trust the list is complete.

**TODOs surfaced:** 1 tooling TODO — generate Materials as a downstream step after D is drafted (see Code / tooling tasks).

**Eval candidate: MAYBE — defer** until after D walkthrough so we can test "every prop mentioned in D appears in C and vice-versa."

### TODO list for prompt updates (surfaced from walkthrough)

Running list. Each item tagged with the section that surfaced it.

- [ ] Decide whether Rule 10's priority order (GC → V → AC) should stand given reference violates it — check with Dr. Farrow (from Section A)
- [ ] **Decontextualization (HIGH)** — v3 examples float free of any unit text; reference grounds examples in a named mentor text (see `lesson-plan-k-example.md:246` citing *Up in the Garden and Down in the Dirt*). Fix options: add optional `unit_text` input (overlaps Rollout #10) and/or prompt rule anchoring examples to a shared text. (from Section B audit)
- [ ] **Application scope creep (MED)** — v3's "Two Sentence Build-It Challenge" (`lc_lesson_K_2026-04-20_025048.md:302–315`) mixes new + previously-learned structures; conflicts with Rule 9's intent that the bridge happens in Review & Connect only. Consider rule: Application stays on new target structure only. (from Section B audit)
- [ ] **Wrap-Up over-reach (LOW)** — v3 adds informational-writing purpose layer not promised in objectives. Likely a strength, not a bug. Re-evaluate during Section D.5 walkthrough before deciding. (from Section B audit)

### Code / tooling tasks (surfaced from walkthrough)

Running list. Changes to the generator script or downstream integration, not to the prompt text itself.

- [ ] Define a Pydantic model for the lesson plan structure and use it as the LLM's structured output schema — locks in section order (Title/Input → A/B/C → D.1–D.5 → Adaptation), field shapes (standards list, objectives list, materials list, D-subsection blocks), and emoji-marker component types. Should eliminate cosmetic drifts (bold-label variance, list-vs-paragraph) so the walkthrough can focus on pedagogical content, not styling. Tentative location: `backend/scripts/prototype_lc_generator.py` (or a sibling `lc_schema.py`). (surfaced 2026-04-20 during walkthrough prep)
- [ ] **Materials section as downstream call** — instead of generating Section C inside the single LLM call, draft A/B/D first, then run a second (chained or parallel) call that extracts the props actually named in D and emits C. Gate on necessity: skip the second pass when D's prop needs are trivial/obvious (heuristic TBD — e.g., activity count, or a coherence check against a first-pass C). Addresses the Materials↔activities coherence gap from Section C walkthrough. Tentative location: `backend/scripts/prototype_lc_generator.py` (add `build_materials_from_draft()`). (surfaced 2026-04-20 during Section C walkthrough)

### Eval candidates (triaged during walkthrough)

Running list. Promote to real eval files once Phase 3 graph integration begins.

- [ ] Standards fidelity eval — codes exist in standards file + descriptions match verbatim + count 1–3 (from Section A)
- [ ] Objective coverage eval — every Section B bullet has ≥1 matching activity in Section D (from Section B)

### Sub-skill consideration

Deferred decision. If the section-walkthrough pattern holds across all 10 sections (especially D.1–D.5 which are content-heavy), consider packaging as `/dev lc-compare <section>` with these capabilities:

- Auto-loads the three files (v3 output, reference, prompt script)
- Pre-locates the section text in all three using markdown heading regex
- Pre-populates the rule-to-section cheat sheet and prompts for findings
- Appends findings to the tracker under the right subsection
- Bumps the section checklist

Decide after finishing all 10 sections; premature sub-skill creation is overhead if the method keeps changing.
