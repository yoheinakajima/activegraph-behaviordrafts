# Live LLM Matrix Results Snapshot

**Substrate-status note (2026-05-23):** This 69-trial snapshot is preserved as historical evidence from pre-native-ActiveGraph/local-shim runs. Do not treat it as current ActiveGraphAdapter+native-runtime performance until the same matrix is rerun on a machine where `import activegraph` succeeds for default backend execution.

## Current primary snapshot (local)

This document records the **current primary local live matrix snapshot** for this repository.

- Date: 2026-05-23
- Model: `gpt-4o-mini`
- Goals: 23
- Trials per goal: 3
- Total trials: 69

> This is a **local result snapshot** from one bounded run context. Future live runs may vary by time, environment, model behavior, and prompt/runtime variance. These results are not a claim of broad LLM reliability.

## Aggregate metrics

| Metric | Value |
|---|---:|
| model | gpt-4o-mini |
| goals | 23 |
| trials_per_goal | 3 |
| total_trials | 69 |
| parsed_ok | 69 |
| static_analysis_passed | 67 |
| sandbox_passed | 64 |
| diff_matches | 59 |
| promotions_succeeded | 59 |
| matching_event_fires | 59 |
| nonmatching_event_silent | 59 |
| disable_succeeded | 59 |
| full_successes | 59 |
| parse_failures | 0 |
| static_failures | 2 |
| sandbox_failures | 3 |
| semantic_failures | 5 |
| promotion_failures | 0 |
| matching_event_failures | 0 |
| nonmatching_event_failures | 0 |
| disable_failures | 0 |

## Failure-stage breakdown

- none: 59
- semantic_diff: 5
- sandbox: 3
- static_analysis: 2

## Goal-level full success counts

- file_summary_1: 2/3
- todo_extract_1: 3/3
- heading_count_1: 3/3
- url_extract_1: 0/3
- todo_extract_2: 3/3
- todo_extract_3: 3/3
- todo_extract_4: 3/3
- missing_prov_1: 3/3
- missing_prov_2: 3/3
- missing_prov_3: 3/3
- missing_prov_4: 3/3
- rel_task_owner: 3/3
- rel_summary_source: 0/3
- rel_eval_proposal: 2/3
- rel_child_parent: 3/3
- schema_violation_1: 3/3
- schema_violation_2: 3/3
- classify_file_py: 2/3
- classify_file_md: 2/3
- classify_priority_high: 3/3
- classify_priority_low: 3/3
- classify_risk_high: 3/3
- classify_risk_low: 3/3

## Known failure cases

- file_summary_1 trial 1: semantic_diff
- url_extract_1 trial 0: sandbox, source_execution_error: name 'next' is not defined
- url_extract_1 trial 1: sandbox, source_execution_error: name 'next' is not defined
- url_extract_1 trial 2: static_analysis, unterminated string literal
- rel_summary_source trials 0,1,2: semantic_diff
- rel_eval_proposal trial 0: semantic_diff
- classify_file_py trial 2: static_analysis, unexpected character after line continuation
- classify_file_md trial 2: sandbox, source_execution_error: object type not allowed

## Surrounding context retained

- deterministic baseline still passes
- adversarial corpus remains 29/29 expectation match
- unexpected passes: 0
- unexpected failures: 0
- live graph violations: 0
- latest tests passed

## Earlier runs (prior snapshots)

Earlier smoke/smaller snapshots (for historical context only) are prior runs and are **not** the current primary result:

- 23-goal / 1-trial run (superseded)
- 2-goal smoke-style runs (superseded)
