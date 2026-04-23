# Language Construction TODO

<!-- Split from main TODO on 2026-04-19 for focused LC tracking. -->
<!-- Managed by /dev sub-skills. Grouped by phase, checkbox style. -->

> Long-form review notes and cycle walkthroughs live in [`LC-review-tracker.md`](LC-review-tracker.md). This file is for actionable tasks only.

## Prototype cycle findings (2026-04-19)

- [x] **Fix K.L.GC.2.c miscoding in LC example lessons** — Reference `lesson-plan-k-example.md` listed `K.L.GC.2.c — Use simple sentences to express complete thoughts in written texts.`; per curated `language-construction-standards.md`, that description actually belongs to `K.L.GC.2.b` ("With adult support, use simple sentences..."). Fixed in both `prompt-ready/lesson-plan-k-example.md` and the comment-bearing duplicate `language_construction/lesson-plan-k-example.md`. Discovered via cycle 3 of `prototype_lc_generator.py`. (2026-04-19)
- [ ] **Flag K.L.GC.2.c → K.L.GC.2.b correction to Dr. Farrow** — In the Phase 2 review email, mention that the standards code in `lesson-plan-k-example.md` was realigned to `K.L.GC.2.b` per the SY2025-2026 GSE source. Confirm she agrees with the change. (2026-04-19)

## Rollout (Dr. Farrow, 2026-04-15)

Ordered by execution path (prototype-first approach). Core path: prep reference materials → build standalone prototype → Dr. Farrow review → integrate. Secondary items (more FORM K activities, extra samples, PreK/1st standards) unblock later phases or improve iteration quality.

**Original commitment (superseded):**

- [ ] **Ship language construction lesson generator by 2026-04-17 EOD** — Original commitment to Dr. Farrow. Superseded 2026-04-17 by prototype-first plan (build standalone → send for review → integrate after approval). Keep here for context; re-word or close once new timeline is agreed with Dr. Farrow. (email thread, 2026-04-15)

**Core path (do in this order):**

- [x] **1. Update language construction standards to new code format (K grade)** — Built `backend/prompt/reference_materials/language-construction-standards.md` with curated K.L.GC, K.L.V, and K.P.AC.2.c codes (narrow filter: syntax + grammar + vocabulary only). Fixed miscoded `K.P.ST.2.c` → `K.P.AC.2.c` in `lesson-plan-k-example.md` along the way. (2026-04-17)
- [x] **2. Convert LC example lessons to emoji notation** — Both example lessons (`form-j-example-lesson.md`, `lesson-plan-k-example.md`) still use Form I's original notation: `[Explanation:...]`, `#Teacher Script:`, `(child response)`, `{Teacher Does}`, `*Modification`, `^Modified script`. Handwriting examples were migrated to emoji markers: 💡 **Explanation**, 🗣️ **Teacher**, 💬 **Child Response**, 👉 **Teacher Does**, 🔄 **Adaptation**. Convert both LC samples to the same convention and update Form I's component legend to match so references and generator prompt stay aligned. Blocks the prototype — prompt should teach the generator emoji output from day one. (scope 2026-04-17)
- [ ] **3. Phase 1: build LC generator prototype (standalone)** — Create `backend/scripts/prototype_lc_generator.py` with hardcoded inputs (K / informational / weather vocab / be-verbs / on-level). Load LC reference materials (Forms I, E, K, M, R + emoji'd examples) + K standards file. Call `gpt-5.4`, write output to file. No graph wiring. Iterate prompt manually against `lesson-plan-k-example.md` as structural-fidelity target (not verbatim). Cross-check against Form J inputs (sea creatures, be-verbs) to catch overfitting. Blocked on: task 2. (scope 2026-04-17)
- [ ] **4. Phase 2: send LC prototype output to Dr. Farrow for review** — Package the best prototype output + system prompt for review. Deliver via usual Dropbox/email path. Blocks Phase 3 until approved. Blocked on: task 3. (scope 2026-04-17)
- [ ] **5. Phase 3: integrate LC generator into graph** — After Dr. Farrow approves: build `backend/app/graph/agents/language_construction_generator.py` + `language_construction_generator_node` in `graph.py`. Replace `vocabulary_generator_placeholder` wiring. Thread modification flow via `lesson_markdown` detection. Connect image pipeline (`image_assembly` → `image_director`). Update `entry_router` for LC modification re-entry. Smoke test + deploy. Blocked on: task 4 approval. (scope 2026-04-17)

**Iteration-quality helpers (run in parallel with core path, each gates on Dr. Farrow's revision turnaround):**

- [ ] **6. Draft additional FORM K activities via ChatGPT** — FORM K alone may not cover the activity range needed. Scope strictly to the 5 sentence-structure verbs: identify, build, imitate, expand, combine. NO mixing with handwriting activities (Dr. Farrow emphatic). Send drafts for her revision. (email reply, 2026-04-15)
- [ ] **7. Draft 3+ language construction sample lesson plans via ChatGPT** — Currently only 2 examples vs. 5 used for handwriting. Quality will suffer without more. Dr. Farrow approved AI drafting; she'll revise. (email reply, 2026-04-15)

**Multi-grade rollout (K prototype proves viability first):**

- [ ] **8. Extend LC standards file to PreK + 1st grade** — K complete. PreK needs curation from `48-60_Indicators.pdf` (GELDS CLL domain — language-construction-relevant indicators only). 1st grade from `Standards Language Arts_Grade 1.pdf` (expected domains: `1.L.GC`, `1.L.V`, `1.P.AC` — mirror K's narrow filter). Pick up in a fresh chat when 1st/PreK prototype becomes priority. (scope 2026-04-17)

**Async cleanup:**

- [ ] **9. Clarify "FORM J codes" question with Dr. Farrow** — She read "codes in old format" as document formatting and was confused. Re-ask if you meant pedagogical/activity codes; otherwise proceed with old-format sample as-is for AI training. (email reply, 2026-04-15)

**LC generator prompt rules (from Dr. Farrow comments on example lessons, 2025-12-09 / 2026-04-15):**

- [ ] **10. LC param agent intake schema** — Collect: unit focus, vocabulary words, genre (narrative/opinion/informational), sentence structure focus, previously-learned sentence structure, grade, ability level (more support / more challenge / on target). Mirrors handwriting param pattern + adds `previously_learned_structure`. (form-j comment 9 + lesson-plan-k comment 5)
- [ ] **11. Activity naming + FORM K hyperlinks** — Each activity in a generated LC lesson must be hyphenated and linkable to its FORM K description (activity name + suggested level). Same pattern as handwriting activity-framework.md. (form-j comment 81)
- [ ] **12. Generator populates example banks inline** — Activities that reference example sentences/word lists must have real content in a 📝 **Example Bank:** block, not placeholders like "+Additional examples". Appears 3× in Form J — recurring pattern. (form-j comments 89, 149, 225)
- [ ] **13. Always-on Adaptation prompt with vary-by-ability** — Every LC lesson ends with 🔄 **Adaptation:** asking for modifications. Modification types span: activity-level, modeling depth, guided-practice pacing, example intensity. Refer to Science of Learning principles. (form-j comment 292)
- [ ] **14. Strip comments from LC example originals once 10–13 are resolved** — Originals in `language_construction/form-j-example-lesson.md`, `lesson-plan-k-example.md`, and `form-l-modifications.md` still carry Dr. Farrow's comment blockquotes. Once items 10–13 are implemented and validated in the prototype/generator, strip the blockquotes and retire the `prompt-ready/` duplicates. (cleanup, 2026-04-17)
