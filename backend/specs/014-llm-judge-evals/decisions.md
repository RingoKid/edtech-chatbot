# 014: LLM Judge Evals — Design Decisions

## 1. Fixtures (Not Regeneration)

- Generated lessons saved as JSON fixtures
- Evals run against fixtures — no LLM generation per eval run
- Regeneration script runs on-demand (after prompt changes)

## 2. Changelog & Versioning

- `changelog.yaml` — structured iteration log (id, date, git_commit, description, changes, results)
- `results/iteration_NNN/` — per-iteration scores + auto-generated summary
- Git tags per iteration (`eval-v001`, etc.)

## 3. Scoring Approach

- Count/classify, not holistic rating
- Judge makes binary decisions per item (is this step sequenced properly? yes/no)
- We compute percentage: `passed / total`
- Reasoning captured per item for drill-down

## 4. Separate Evals (Not One Big Call)

- Each sub-dimension = independent eval with its own judge prompt
- Can run in parallel on same fixture
- Composite = mean of individual scores

## 5. First Eval Cluster: Scaffolding (Rubric Criteria 1+2+3)

- `scaffolding_within_activity` — sub-steps ordered easy→hard per activity
- `scaffolding_between_activity` — complexity builds across sections 1→5
- `scaffolding_gradual_release` — teacher support decreases (pairwise transitions)
- `scaffolding_level_appropriate` — activities match student level (Form D levels)

## 6. Not Decided Yet

- Judge model (gpt-4o-mini? gpt-4o? same as generator?)
- Fixture format details (exact JSON schema)
- Remaining rubric criteria mapping (criteria 4-10)
- Thresholds for pass/fail per eval
