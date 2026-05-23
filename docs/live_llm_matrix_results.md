# Live LLM Matrix Results Snapshot

## Current primary snapshot: post-ActiveGraphAdapter local live run (2026-05-23)

This document records the **current primary** live matrix result for this repository.

### Run context

- Run location: local
- Backend kind: `activegraph_adapter`
- ActiveGraph available locally: `true`
- Model: `gpt-4o-mini`
- Goals: 23
- Trials per goal: 3
- Total trials: 69
- Generated `results/*` artifacts are untracked by design and are not source-of-truth files to commit.

> A post-ActiveGraphAdapter 23-goal / 69-trial live matrix with gpt-4o-mini produced 60 full lifecycle successes. All attempts parsed, and all failures were caught before authority transfer. No promotion, matching-event, nonmatching-event, or disable checks failed once semantic diff passed.

## Aggregate metrics

| Metric | Value |
|---|---:|
| model | gpt-4o-mini |
| goals | 23 |
| trials_per_goal | 3 |
| total_trials | 69 |
| parsed_ok | 69 |
| static_analysis_passed | 65 |
| sandbox_passed | 63 |
| diff_matches | 60 |
| promotions_succeeded | 60 |
| matching_event_fires | 60 |
| nonmatching_event_silent | 60 |
| disable_succeeded | 60 |
| full_successes | 60 |
| parse_failures | 0 |
| static_failures | 4 |
| draft_construction_failures | 0 |
| test_construction_failures | 0 |
| sandbox_failures | 2 |
| semantic_failures | 3 |
| promotion_failures | 0 |
| matching_event_failures | 0 |
| nonmatching_event_failures | 0 |
| disable_failures | 0 |

## Per-goal full success outcomes

| Goal | Full successes |
|---|---:|
| classify_file_md | 3/3 |
| classify_file_py | 3/3 |
| classify_priority_high | 3/3 |
| classify_priority_low | 3/3 |
| classify_risk_high | 3/3 |
| classify_risk_low | 3/3 |
| file_summary_1 | 3/3 |
| heading_count_1 | 3/3 |
| missing_prov_1 | 3/3 |
| missing_prov_2 | 3/3 |
| missing_prov_3 | 3/3 |
| missing_prov_4 | 3/3 |
| rel_child_parent | 3/3 |
| rel_eval_proposal | 3/3 |
| rel_summary_source | 0/3 |
| rel_task_owner | 3/3 |
| schema_violation_1 | 3/3 |
| schema_violation_2 | 3/3 |
| todo_extract_1 | 2/3 |
| todo_extract_2 | 2/3 |
| todo_extract_3 | 3/3 |
| todo_extract_4 | 2/3 |
| url_extract_1 | 0/3 |

## Failure-stage breakdown

| Failure stage | Count |
|---|---:|
| none | 60 |
| static_analysis | 4 |
| sandbox | 2 |
| semantic_diff | 3 |

## Known failure cases

| Case | Stage | Detail |
|---|---|---|
| todo_extract_1 trial 2 | static_analysis | f-string expression part cannot include a backslash |
| url_extract_1 trial 0 | sandbox | name `next` is not defined |
| url_extract_1 trial 1 | static_analysis | unterminated string literal |
| url_extract_1 trial 2 | sandbox | name `next` is not defined |
| todo_extract_2 trial 2 | static_analysis | f-string expression part cannot include a backslash |
| todo_extract_4 trial 2 | static_analysis | unexpected character after line continuation |
| rel_summary_source trials 0,1,2 | semantic_diff | semantic mismatch |

## Deterministic/adversarial context after ActiveGraphAdapter

- `backend_kind`: `activegraph_adapter`
- `activegraph_available`: `true`
- Native features include `activegraph.Graph`, `activegraph.Runtime`, `activegraph.Event`, `activegraph.Behavior`, `Graph.add_object`, `Graph.add_relation`, `Graph.emit`, `Runtime.fork`, `Runtime.diff`.
- Adapter shims include `behavior_dispatch_adapter`, `dynamic_behavior_registration_adapter`, `disable_metadata_adapter`, `diff_normalization_adapter`, `snapshot_diff_adapter`.
- Deterministic runs: 6
- Adversarial cases: 29
- Cases matching expectation: 29
- Unexpected passes: 0
- Unexpected failures: 0
- Promotions succeeded: 2
- Live graph violations: 0
- Tests: 76 passed

## Interpretation for paper

This run supports a bounded, auditable lifecycle claim: generated behavior can pass staged gates and reach live scoped behavior when outputs are semantically correct, while failures are blocked before promotion.

### Explicit non-claims

- Not a claim of broad LLM reliability.
- Not a claim of open-ended recursive self-improvement.
- Not a claim of full Python sandbox security.
- Not a claim of secure arbitrary code execution.
- Not a broad task-performance benchmark.
- Adapter still uses documented shims.

## Earlier snapshots (historical only)

- Pre-ActiveGraphAdapter local-shim 23-goal/69-trial snapshot: **59/69** full lifecycle successes.
- Two-goal smoke-style runs: superseded by larger matrix runs.
