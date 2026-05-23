# Live LLM Matrix Results Snapshot

## 1. Run context

- Date: 2026-05-23 (timestamp shown in attached run output: `2026-05-23T02:31:05+00:00`).
- Execution context: local run output captured outside Codex.
- Model: `gpt-4o-mini`.
- Command/run type: local live matrix and paper-table generation (`python scripts/run_live_llm_matrix.py --trials 1` and `python scripts/generate_paper_tables.py`).
- Generated `results/` artifacts are intentionally untracked by repository policy.

## 2. Aggregate result

| Metric | Value |
|---|---:|
| model | gpt-4o-mini |
| goals | 23 |
| trials_per_goal | 1 |
| total_trials | 23 |
| parsed_ok | 23 |
| static_analysis_passed | 23 |
| sandbox_passed | 23 |
| diff_matches | 22 |
| promotions_succeeded | 22 |
| matching_event_fires | 22 |
| nonmatching_event_silent | 22 |
| disable_succeeded | 22 |
| full_successes | 22 |
| parse_failures | 0 |
| static_failures | 0 |
| sandbox_failures | 0 |
| semantic_failures | 1 |
| promotion_failures | 0 |
| matching_event_failures | 0 |
| nonmatching_event_failures | 0 |
| disable_failures | 0 |
| surrounding_pytest_passed | 64 |
| adversarial_cases_matching_expectation | 29/29 |
| adversarial_unexpected_passes | 0 |
| adversarial_unexpected_failures | 0 |
| adversarial_live_graph_violations | 0 |

## 3. Per-goal outcome summary

| Goal | Trials | Full successes |
|---|---:|---:|
| file_summary_1 | 1 | 1 |
| todo_extract_1 | 1 | 1 |
| heading_count_1 | 1 | 1 |
| url_extract_1 | 1 | 1 |
| todo_extract_2 | 1 | 1 |
| todo_extract_3 | 1 | 1 |
| todo_extract_4 | 1 | 1 |
| missing_prov_1 | 1 | 1 |
| missing_prov_2 | 1 | 1 |
| missing_prov_3 | 1 | 1 |
| missing_prov_4 | 1 | 1 |
| rel_task_owner | 1 | 1 |
| rel_summary_source | 1 | 0 |
| rel_eval_proposal | 1 | 1 |
| rel_child_parent | 1 | 1 |
| schema_violation_1 | 1 | 1 |
| schema_violation_2 | 1 | 1 |
| classify_file_py | 1 | 1 |
| classify_file_md | 1 | 1 |
| classify_priority_high | 1 | 1 |
| classify_priority_low | 1 | 1 |
| classify_risk_high | 1 | 1 |
| classify_risk_low | 1 | 1 |

## 4. Failure analysis

Single failed case from the attached run output:

- `goal_id`: `rel_summary_source`
- `failure_stage`: `semantic_diff`
- `parsed_ok`: `true`
- `static_analysis_passed`: `true`
- `sandbox_passed`: `true`
- `diff_match`: `false`
- `promotion_succeeded`: `false`
- `source_execution_error`: `null`
- `static_analysis_errors`: `[]`

Interpretation: this was a semantic mismatch caught before promotion/authority transfer, not a parse, static-analysis, sandbox, promotion-runtime, or execution error.

## 5. Paper relevance

This snapshot materially strengthens the paper’s empirical section by extending from a two-goal smoke-test framing to a bounded 23-goal local live matrix result with 22/23 full lifecycle successes.

Safe claim: a bounded 23-goal live matrix with `gpt-4o-mini` showed 22/23 full lifecycle successes; the one failure was caught by semantic diff before authority transfer.

Non-claims (explicitly out of scope):

- broad LLM reliability,
- open-ended self-improvement,
- full Python sandbox security,
- production security proof,
- broad task-performance benchmarking.

## 6. Relationship to generated artifacts

- `results/live_llm_matrix_summary.json` and related `results/` files are generated outputs and intentionally untracked.
- This document (`docs/live_llm_matrix_results.md`) is the tracked, human-readable snapshot of the local run outcome.
- Re-running the live matrix in the future may produce different numbers.

## 7. Next step

Recommended next step: run `--trials 3` across the same 23-goal matrix to estimate stability/variance instead of relying on a single trial per goal.
