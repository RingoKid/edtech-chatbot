# Planner Directives Eval — 2026-04-06 05:25:34

**Git SHA**: `eeb5fd5`
**Duration**: 32.5s
**Overall**: 69/70 checks passed (99%)

## Results by Fixture

### prek_m_struggling — PASS (7/7, 100%)

Params: grade=PreK, letter=m, level=struggling

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['single_sound'] | single_sound | pass |
| include_directionality | True | True | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['magic_finger_write', 'trace_and_say', 'write_and | ['magic_finger_write', 'trace_and_say', 'write_and | pass |
| scaffolding_intensity | heavy | heavy | pass |
| content_scope | >=2 sentences, >=40 chars | (272 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### prek_s_onlevel — PASS (7/7, 100%)

Params: grade=PreK, letter=s, level=on-level

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['single_sound'] | single_sound | pass |
| include_directionality | True | True | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['magic_finger_write', 'trace_and_say', 'write_and | ['magic_finger_write', 'trace_and_say', 'write_and | pass |
| scaffolding_intensity | heavy | heavy | pass |
| content_scope | >=2 sentences, >=40 chars | (247 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### prek_t_advanced — PASS (7/7, 100%)

Params: grade=PreK, letter=t, level=advanced

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['single_sound'] | single_sound | pass |
| include_directionality | True | True | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['magic_finger_write', 'trace_and_say', 'write_and | ['magic_finger_write', 'trace_and_say', 'write_and | pass |
| scaffolding_intensity | heavy | heavy | pass |
| content_scope | >=2 sentences, >=40 chars | (294 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### k_b_struggling — PASS (7/7, 100%)

Params: grade=K, letter=b, level=struggling

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC'] | CVC | pass |
| include_directionality | True | True | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['magic_finger_write', 'trace_and_say', 'write_and | ['magic_finger_write', 'trace_and_say', 'write_and | pass |
| scaffolding_intensity | heavy | heavy | pass |
| content_scope | >=2 sentences, >=40 chars | (473 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### k_d_onlevel — PASS (7/7, 100%)

Params: grade=K, letter=d, level=on-level

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC'] | CVC | pass |
| include_directionality | False | False | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['trace_and_say', 'say_and_write', 'write_and_say' | ['trace_and_say', 'say_and_write', 'write_and_say' | pass |
| scaffolding_intensity | moderate | moderate | pass |
| content_scope | >=2 sentences, >=40 chars | (392 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### k_w_advanced — PASS (7/7, 100%)

Params: grade=K, letter=w, level=advanced

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC'] | CVC | pass |
| include_directionality | False | False | pass |
| include_articulation | True | True | pass |
| guided_practice_techniques | ['say_and_write', 'write_and_say', 'write_and_soun | ['say_and_write', 'write_and_say', 'write_and_soun | pass |
| scaffolding_intensity | moderate | moderate | pass |
| content_scope | >=2 sentences, >=40 chars | (346 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### first_p_struggling — PASS (7/7, 100%)

Params: grade=1st, letter=p, level=struggling

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC', 'CCVC', 'CVCC'] | CVC | pass |
| include_directionality | False | False | pass |
| include_articulation | False | False | pass |
| guided_practice_techniques | ['say_and_write', 'write_and_say', 'write_and_soun | ['say_and_write', 'write_and_say', 'write_and_soun | pass |
| scaffolding_intensity | moderate | moderate | pass |
| content_scope | >=2 sentences, >=40 chars | (436 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### first_i_onlevel — PASS (7/7, 100%)

Params: grade=1st, letter=i, level=on-level

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVCe'] | CVCe | pass |
| include_directionality | False | False | pass |
| include_articulation | False | False | pass |
| guided_practice_techniques | ['cover_and_try', 'say_and_write', 'write_and_soun | ['cover_and_try', 'say_and_write', 'write_and_soun | pass |
| scaffolding_intensity | light | light | pass |
| content_scope | >=2 sentences, >=40 chars | (421 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

### first_a_struggling — FAIL (6/7, 86%)

Params: grade=1st, letter=a, level=struggling

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC'] | CVC | pass |
| include_directionality | False | False | pass |
| include_articulation | False | False | pass |
| guided_practice_techniques | ['say_and_write', 'write_and_say', 'write_and_soun | ['say_and_write', 'write_and_sound', 'write_and_so | **FAIL** |
| scaffolding_intensity | moderate | moderate | pass |
| content_scope | >=2 sentences, >=40 chars | (373 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

**Failures:**
- `guided_practice_techniques`: got ['say_and_write', 'write_and_sound', 'write_and_sound'], expected ['say_and_write', 'write_and_say', 'write_and_sound']

### first_r_advanced — PASS (7/7, 100%)

Params: grade=1st, letter=r, level=advanced

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| spelling_pattern | ['CVC', 'CCVC', 'CVCC'] | CVC | pass |
| include_directionality | False | False | pass |
| include_articulation | False | False | pass |
| guided_practice_techniques | ['cover_and_try', 'disappearing_letter', 'write_an | ['cover_and_try', 'disappearing_letter', 'write_an | pass |
| scaffolding_intensity | light | light | pass |
| content_scope | >=2 sentences, >=40 chars | (476 chars, 3 sentences) | pass |
| all_fields_present | not all defaults | fields populated | pass |

## Summary

| Fixture | Score |
|---------|-------|
| prek_m_struggling | 100% |
| prek_s_onlevel | 100% |
| prek_t_advanced | 100% |
| k_b_struggling | 100% |
| k_d_onlevel | 100% |
| k_w_advanced | 100% |
| first_p_struggling | 100% |
| first_i_onlevel | 100% |
| first_a_struggling | 86% |
| first_r_advanced | 100% |