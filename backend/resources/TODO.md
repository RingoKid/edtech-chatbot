# Project TODO

<!-- Managed by /dev sub-skills. Grouped by source, checkbox style. -->

## Async/Performance Fixes (audit, 2026-03-17)

- [x] **Sync DynamoDB calls block event loop** — `chat_history_service.py`, `auth_service.py`, `feedback_service.py` all declare `async def` but call blocking boto3 methods (`table.put_item`, `table.query`, etc.). Every DB call serializes the event loop — 2 concurrent users block each other. Fix: wrap in `asyncio.to_thread()` or switch to `aioboto3`.
- [x] **Graph nodes use sync `.invoke()` in async context** — `graph.py` nodes (`routing_agent_node`, `param_agent_node`, `handwriting_generator_node`, `feedback_collector_node`) call `agent.invoke()` synchronously. The outer `handle_message()` uses `await graph.ainvoke()` but each node blocks the loop during LLM calls. Fix: switch to `await agent.ainvoke()` and make nodes async.
- [x] **Fire-and-forget image generation task** — `image_director.py:99-101` creates background task with `asyncio.create_task()` but never awaits or handles errors. Graph returns before images exist; failures are silent. Fix: await the task or add error handling + logging.
- [x] **Module-level blocking DynamoDB import** — `database.py:38-41` calls `get_dynamodb_resource()` and `dynamodb.Table()` at import time. If DynamoDB is slow/unavailable, entire app hangs on startup. Fix: lazy-load on first request.
- [x] **Graph lazy-init race condition** — `chat_service.py:33-40` `_get_graph()` checks `if self._graph is None` without a lock. Concurrent requests can call `create_graph()` multiple times. Fix: use `asyncio.Lock`.
- [x] **Mixed sync/async graph node signatures** — `graph.py` has some nodes sync, some async (`image_director_node`, `image_assembly_node`). LangGraph handles this but it's inconsistent and error-prone. Fix: make all nodes async.
- [x] **Deprecated `asyncio.get_event_loop()`** — `image_service.py:204` uses deprecated pattern. Fix: use `asyncio.get_running_loop()`.
- [x] **No app lifecycle handlers** — `main.py` has no startup/shutdown hooks. Langfuse client never flushed, DynamoDB connections never closed, background tasks not cancelled on shutdown. Fix: add FastAPI lifespan context manager.
- [x] **Blocking password hashing in async routes** — `auth.py` calls bcrypt `get_password_hash()` / `verify_password()` synchronously in async route handlers. CPU-bound, blocks event loop under load. Fix: wrap in `asyncio.to_thread()`.

## Reference Material Updates (Dr. Farrow, 2026-03-16)

- [x] **Update Form D** — Replaced by activity-framework.md + activity-index.yaml in spec 023. Form D still on disk for reference but no longer loaded by generator or evals.
- [x] **Add Activity Framework** — Added as `activity-framework.md` with slug headings for regex extraction. Used by planner and generator via dispatcher pattern. (commits `284302f`, `bc3406e`)
- [ ] **Add First Grade Scripted Lesson** — Dr. Farrow's hand-written reference lesson (3 comments, Feb 21). Not in codebase. Dropbox: `First grade scripted lesson .docx`. Converted markdown at `/tmp/first-grade-scripted-lesson.md`.
  - **Files:** source `/tmp/first-grade-scripted-lesson.md`, destination `backend/prompt/reference_materials/handwriting/` (decide filename), `backend/app/graph/agents/handwriting_generator.py` (register in `UNIVERSAL_FORM_FILES` or add as a variant Form C — see `GRADE_TO_FORM_C_FILE`), `backend/resources/docs-manifest.json` (track source).

## Generator Prompt Changes (Dr. Farrow feedback, 2026-03-09)

- [x] **AI does not prompt for previously learned skills** — Fixed in spec 023. Added `previously_learned` intake question + Rule 12 constrains word choices to taught sounds only.
- [x] **Activity name confusion** — Fixed by planner pipeline. Activities selected by slug, descriptions extracted by regex, names displayed from framework headings. Activity naming eval now scores 100%.
- [x] **Review section incorrect** — Fixed by Rule 12 clause: Section 1 must use only `previously_learned` sounds; target letter MUST NOT appear until Section 2. Validated on k_letter_b_onlevel_mid 2026-04-23 — Section 1 drills `map, cat, jam`, no /b/ until Section 2.
- [x] **Form B explanations not verbatim** — Fixed by Rule 1 anti-placeholder clause (forbids `(Use Form B explanation here)`, etc.). Validated 2026-04-23 — all 5 sections open with literal "The purpose of this part of the lesson is to…".
- [x] **Lowercase only by default for K** — Resolved: letter case determined by teacher input (lowercase `b` → lowercase lesson, uppercase `B` → uppercase). Removed `.upper()` calls in generator. (spec 023 phase 2)
- [x] **Verbal cues not populated** — Fixed by Rule 2 anti-placeholder clause (forbids `(Insert verbal cues)`, `[verbal cues from Form F]`, etc.). Validated 2026-04-23 — ✏️ markers contain literal stroke cues.
- [ ] **Guided practice sequencing wrong for K** — "by kindergarten they should be able to first trace then try their own on level — if children are struggling learners then air writing is more appropriate to begin" — Magic Finger Write not appropriate for on-level K. (comment #13)
  - **Files:** `backend/app/graph/agents/activity_planner.py` (planner picks `guided_practice_techniques` list — needs K+on-level rule to skip air-writing techniques), `backend/app/graph/state.py` (`ActivityPlan` schema, `guided_practice_techniques` field), `backend/prompt/reference_materials/handwriting/activity-framework.md` (technique definitions — confirm which are air-writing vs pencil-in-hand).
- [ ] **Trace & Say confusion** — "trace and say means kids are actually writing, pencil in hand" — generator showed finger-on-picture instead. (comment #15)
  - **Files:** `backend/prompt/reference_materials/handwriting/activity-framework.md` (find the "Trace & Say" slug — check whether its description is ambiguous about finger-on-picture vs pencil-in-hand). Likely a reference-material clarification, not a generator prompt fix.
- [x] **Say sound while writing, not letter name** — Fixed by Rule 11 bullet: when children write the target letter they say /{letter}/, not the name. Validated 2026-04-23 — script explicitly says "as you write, just say the sound /b/. Not the letter name."
- [x] **Application section had no priming** — Fixed by Rule 7 priming-transition clause: Section 4 must open with a grade-specific line naming the leap to encoding (e.g., K: "Now we're going to use /{letter}/ to spell real words — like a real speller would."). Validated 2026-04-23 — K/B fixture has 6 priming signals including "like a real speller" 3x.
- [ ] **Need to prompt for previously learned skills** — Required so AI can select logical activity sequences and appropriate word examples. (comments #19, #21)
  - **Files:** `backend/app/graph/agents/param.py` (HandwritingParams schema — confirm `previously_learned` has no default), `backend/app/graph/state.py` (state shape), `backend/app/graph/agents/handwriting_generator.py` (Rule 12 consumes it). LIKELY STALE — spec 023 already added the intake question; verify against current param schema before marking done.
- [x] **Teacher giving away answers** — Fixed by Rule 9 "Elicit BEFORE Tell" pre-response clause: question + 💬 Child Response must appear before teacher confirms. Phrased as pre-response to avoid conflicting with Rule 9's post-response explanation. Validated 2026-04-23.
- [x] **Word choice issues** — Fixed by Rule 12 exclusion list (`on, the, was, said, of, is, has, his, to, you, I, a, my, be, are`). Validated 2026-04-23 — example words are all decodable CVC.
- [x] **Sound/letter comparison inappropriate without prior teaching** — Fixed by Rule 10 clause: `[confusable]` partner must be in `previously_learned`, or skip the comparison. Validated 2026-04-23 — b/p comparison used /p/ which is in previously_learned.

## Layout/UX Changes (Dr. Farrow feedback, 2026-03-09)

- [ ] **Corrective feedback should be boxed** — "teachers know it is not part of the lesson but is a way teachers can correct misunderstandings" (rubric comment #1)
  - **Files:** `backend/app/graph/agents/handwriting_generator.py` Rule 8 (Corrective Feedback block — currently plain bold label, needs a box syntax convention — maybe `> **Corrective Feedback:**` markdown blockquote or a new emoji/marker). `frontend/src/components/` (markdown renderer — check if blockquote renders as boxed; may need custom component). Decide convention before editing.
- [ ] **Add boxed section for possible words/sounds** — "Teachers like to see that" — after each activity, show all possible words/letter sounds to use. (rubric comment #1)
  - **Files:** `backend/app/graph/agents/handwriting_generator.py` (add a rule requiring a "Possible words/sounds" block after each activity), frontend markdown renderer (same render concern as Corrective Feedback boxing above — should share the convention).

## Bug Fixes (Dr. Farrow, 2026-03-14)

- [ ] **Old lesson plan conversations not shown in queue** — "my old lesson plans 'conversations' are not being shown in the queue" (email #4, Mar 14)
  - **Files:** `backend/app/services/chat_history_service.py` (how historical conversations are listed for a user), `backend/app/api/` (queue endpoint — grep for the route), `frontend/src/` conversation-queue component (grep for "queue" or "history"). Likely a query filter excluding older/completed/finalized conversations.

## Activity Planner (spec 023, 2026-04-03)

- [x] **Fix standards selection pipeline** — Implemented: `extract_standard()`, `validate_plan_standards()`, planner prompt with grade-filtered standards, generator Rule 5 rewritten to use pre-selected standards. All 34 codes validated, fabricated codes eliminated. (commit `ee66f1f`)
- [x] **Update activity_naming eval rubric** — All 5 eval rubrics updated from Form D to activity-framework.md. Eval runner loads `activity-framework.md` instead of `form-d-scaffolded-activities.md`. Activity naming now scores 100%. (commit `3572ca1`)
- [x] **Update eval Pydantic models** — `tests/evals/models.py` field descriptions updated from "Form D" to "activity framework". (commit `98b99d1`)
- [x] **Upgrade models to GPT-5.4 family** — All nodes upgraded: routing/param/planner/feedback → gpt-5.4-mini, generator → gpt-5.4. Model registry updated with pricing. (commits `e32dd48`, `98b99d1`)
- [x] **Regenerate all fixtures** — Stale fixtures removed. 5 expert-mirror fixtures regenerated with directive pipeline (2026-04-06). `k_letter_b_struggling_mid` now works.
- [ ] **Add eval for previously-learned-skills prompting** — New behavior from spec 023, needs validation that generator only uses sounds from `previously_learned` list in example words.
  - **Files:** `backend/tests/evals/test_handwriting_generator.py` (add new test case), `backend/tests/evals/rubrics/` (new rubric judging whether example words decode from `previously_learned + target` only), `backend/tests/fixtures/handwriting_generator/k_letter_b_struggling_mid.json` (fixture with limited `previously_learned` list — good test case).

## Generator Quality Issues (expert comparison, 2026-04-06)

Post-directive changes: Structure 100% (all 5 fixtures). Expert comparison scores: PreK/Z 8/10, K/B on-level 7.5/10, K/B struggling 7/10, K/B scaffolded 7.5/10, **1st/I 8/10** (was 4/10). Remaining gaps:

- [x] **1st grade produces intro lesson instead of CVCe** — Fixed by lesson directives (spec 023 phase 2). Planner now outputs `spelling_pattern: CVCe` for 1st + vowel + on-level. Generator contrasts CVC vs CVCe pairs (pip/pipe, kit/kite). Score: 4/10 → 8/10.
- [x] **Guided Practice density** — Fixed by `guided_practice_techniques` directive. Planner specifies ordered technique list (e.g., `[cover_and_try, say_and_write, write_and_sound]`). Generator now produces 3 sub-activities matching expert.
- [ ] **No lesson variant awareness** — Expert "scaffolded" variant uses pre-filled vowels in Application (only write consonants, vowel pre-populated in Elkonin box). Generator has no concept of this — produces standard CVC encoding. May need a `lesson_variant` or `scaffolding_level` parameter.
  - **Files:** `backend/app/graph/state.py` (add `lesson_variant` or `scaffolding_level` to `HandwritingParams` and `ActivityPlan`), `backend/app/graph/agents/param.py` (intake question if user-selectable, or derived from student_level), `backend/app/graph/agents/activity_planner.py` (planner sets variant directive), `backend/app/graph/agents/handwriting_generator.py` (generator consumes directive, e.g., pre-fills vowel letters in Application Elkonin boxes). Cross-reference expert fixture `backend/tests/fixtures/handwriting_expert/expert_k_letter_b_scaffolded.json` for target behavior.
- [x] **Word list poverty** — Fixed by Rule 12 word-count-minimums clause: 8+ unique decodable words in Guided Practice, 6+ more in Application (no repeats), minimal-pair contrasts allowed to reach the minimum. Validated 2026-04-23 — k_letter_b_onlevel_mid Application section grew from previous gen (4718 chars, substantial word extension).
- [x] **Teacher voice too clinical** — Fixed by Rule 11 warmth clause: explicit USE list ("kiss your brains", "my turn/your turn", "show me/watch me", "stretch the sounds", "boys and girls") + AVOID list ("That is correct because", "The answer is correct", "Affirmative"). At least one warmth marker per section. Validated 2026-04-23 — K/B fixture has 38 warmth hits, zero clinical banned phrases (was 5 "That is correct because" in old 1st-grade fixture).
- [x] **Planner `first_r_advanced` spelling_pattern bug** — Fixed by adding two PARALLEL worked examples below the spelling_pattern table in `activity_planner.py` — one vowel case (1st + `i` + on-level → CVCe) and one consonant case (1st + `r` + advanced → CVC/CCVC/CVCC), plus an explicit 2-step decision procedure (Step 1: is letter a vowel? Step 2: apply student_level branch). First attempt with consonant-only counter-example regressed `first_i_onlevel` 3/3; parallel examples fixed both. Validated 2026-04-23 — full eval 70/70 × 2 consecutive runs (was 69/70 pre-fix with `first_r_advanced` failing 3/3).
- [ ] **Enforce lesson structure via Pydantic schema, not prompt rules** — Generator relies entirely on prompt Rule 5 (sections A-D) and Rule 13 (3× `IMAGE_N` placeholders) in `handwriting_generator.py`; `lesson_markdown` is just `Optional[str]` in state. Model can silently drop sections or image placeholders. Fix: define `LessonPlan` Pydantic model, pass via `create_agent(response_format=...)`, then re-serialize to markdown for teacher output + image pipeline. (codebase audit, 2026-04-20)
  - **Files:** `backend/app/graph/agents/handwriting_generator.py` (`DEFAULT_HANDWRITING_GENERATOR_PROMPT` string, Rule 5 around section enumeration, Rule 13 for `IMAGE_N`, `create_agent()` call at bottom — needs `response_format=LessonPlan`), `backend/app/graph/state.py` (currently `lesson_markdown: Optional[str]` — replace with structured type or add parallel `lesson_plan: LessonPlan`), `backend/app/services/image_service.py` (consumes `IMAGE_N` placeholders — update to iterate over structured image slots), `backend/app/graph/graph.py` (generator node — re-serialize structured output to markdown for teacher display).
  - **Reminder:** discuss whether to also inject section headers + Form B verbatim explanations via Pydantic `computed_field` (vs. plain template injection). Decide during implementation. If done via `computed_field`, Rules 1 and 2 anti-placeholder clauses may become redundant and can be trimmed.

## Param Agent (2026-04-06)

- [ ] **Param agent skips previously_learned and skill_focus** — Agent submits tool call after collecting just grade + letter, skipping optional fields. Root cause: Pydantic schema had `default=[]` and `default="isolating_sounds"`. Defaults removed — agent now must provide all fields. But no multi-turn eval exists to catch this regression.
  - **Files:** `backend/app/graph/agents/param.py` (confirm `HandwritingParams` schema has no defaults on `previously_learned` and `skill_focus`), `backend/tests/evals/test_param_agent.py` (where a multi-turn regression eval would live).
- [ ] **Update param eval to check all 5 fields** — `params_to_dict()` (now `extract_full_params`) in `test_param_agent.py` needs to check `previously_learned` and `skill_focus` in addition to grade/letter/student_level.
  - **Files:** `backend/tests/evals/test_param_agent.py` (`extract_full_params` helper around line 40 — walkthrough noted this may already be done; verify before marking).
- [ ] **Add multi-turn param eval** — Test that agent asks all questions before submitting. Flow: send grade → assert no submission → send letter → assert no submission → send previously_learned → assert no submission → send skill_focus → assert extraction with all 5 fields. Current eval only tests single-message extraction.
  - **Files:** `backend/tests/evals/test_param_agent.py` (needs a new multi-turn helper or modify existing single-turn harness — check how the param agent's state is advanced across turns via the `GraphState` in `backend/app/graph/state.py`).
- [ ] **Add "partial info should not submit" test cases** — Cases like "PreK letter m" (has grade + letter but missing previously_learned/skill_focus) should assert `handwriting_params is None` — agent should ask follow-ups, not submit.
  - **Files:** `backend/tests/evals/test_param_agent.py` (add test cases with partial inputs). Assertion target: `handwriting_params` field on state should be `None` when fields are missing.

## Eval Maintenance

- [x] **1st grade marker formatting** — Fixed by Rule 4 reinforcement clause. Validated 2026-04-23 — first_letter_i_onlevel_mid fixture shows 5 💡 / 82 🗣️ / 50 💬 / 10 👉 / 2 🤚 / 3 ✏️ / 1 🔄, zero bracketed notation in any form.
- [ ] **Update scaffolding eval Pydantic models** — `Activity.difficulty_level` still uses `Literal["low", "middle", "high"]` from old Form D system. Framework uses rank (1-7). Judge maps rank→labels naturally for now but schema should align with rank system eventually.
  - **Files:** `backend/tests/evals/models.py` lines ~10-19 (`Activity.difficulty_level` Literal → `rank: int = Field(ge=1, le=7)`), `backend/tests/evals/rubrics/` (rubric prompts using this schema — may need tweak), `backend/tests/evals/test_handwriting_generator.py` or scaffolding-specific eval file (confirm `ActivityPair.correctly_ordered` logic still works with rank comparisons). Low-risk — scoring driver is `correctly_ordered`, not the label itself.

## Pending: Dr. Farrow Review (sent 2026-04-06)

- [ ] **Process lesson plan comments** — 5 lesson plans sent for review in Dropbox `AI Lesson Review - April 2026`. When Dr. Farrow comments, pull feedback with `/dev docs` and add to TODO as generator prompt fixes.
  - **Files:** Dropbox `~/Library/CloudStorage/Dropbox/Handwriting & Spelling (Transcription) AI Codes/AI Lesson Review - April 2026/` (monitor for .docx comments), `/dev docs` skill at `.claude/commands/dev/docs.md` (use to convert .docx → markdown preserving author/date), `backend/resources/expert-feedback/` (destination for processed feedback), `backend/resources/TODO.md` (add new prompt-fix items as they surface). BLOCKED on Dr. Farrow.
- [ ] **Update expert examples with new questions** — Asked Dr. Farrow to add `previously_learned` and `skill_focus` answers to 3 expert files in `Expert Examples (Please Update)` subfolder. Once updated, regenerate expert fixtures in `tests/fixtures/handwriting_expert/`.
  - **Files:** Dropbox `~/Library/CloudStorage/Dropbox/Handwriting & Spelling (Transcription) AI Codes/Expert Examples (Please Update)/` (3 files pending her updates), `backend/scripts/create_expert_fixtures.py` (regen script — check its CLI and input format), `backend/tests/fixtures/handwriting_expert/*.json` (target — regenerate after params are added). BLOCKED on Dr. Farrow.

## DevOps (2026-03-24)

- [ ] **Get OpenAI Admin API key for billing checks** — Need to contact Dr. Farrow. Current `/dev health` only validates the key works; with an Admin key we can check account balance/spend via `/v1/organization/costs`. Add to `/dev health` once obtained.
  - **Files:** `.claude/commands/dev/health.md` (where `/dev health` is defined — add balance/spend check calling OpenAI `/v1/organization/costs`), `backend/.env.local` or AWS SSM (secure store for the admin key — do NOT commit), `backend/app/config.py` or equivalent (load key if any backend-side check is added). BLOCKED on Dr. Farrow.
- [x] **Fix broken CI/CD pipeline** — CodePipeline `edtech-chatbot-develop` was deleted. Recreated with existing CodeBuild project + CodeStar GitHub connection. First deploy succeeded 2026-04-06.

## Existing TODO (from memory)

- [x] **Add skill focus intake question** — Implemented in spec 023 (activity planner). Added to `HandwritingParams` and param agent.
