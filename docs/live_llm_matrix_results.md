# Live LLM Matrix Results Snapshot

## 1. Run context

- This snapshot reflects a **local terminal run** (not a Codex execution).
- Model: `gpt-4o-mini`.
- Corpus size: 23 goals.
- Trials per goal: 3.
- Generated `results/*` files are intentionally untracked artifacts in this repository.
- This tracked documentation snapshot was created from attached terminal output.
- Surrounding run context preserved from the source output:
  - deterministic baseline still passes,
  - adversarial corpus remains 29/29 expectation match,
  - unexpected passes: 0,
  - unexpected failures: 0,
  - live graph violations: 0,
  - tests passed in the run.

## 2. Aggregate result

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

## 3. Per-goal outcomes

| Goal | Trials | Full successes |
|---|---:|---:|
| file_summary_1 | 3 | 2 |
| todo_extract_1 | 3 | 3 |
| heading_count_1 | 3 | 3 |
| url_extract_1 | 3 | 0 |
| todo_extract_2 | 3 | 3 |
| todo_extract_3 | 3 | 3 |
| todo_extract_4 | 3 | 3 |
| missing_prov_1 | 3 | 3 |
| missing_prov_2 | 3 | 3 |
| missing_prov_3 | 3 | 3 |
| missing_prov_4 | 3 | 3 |
| rel_task_owner | 3 | 3 |
| rel_summary_source | 3 | 0 |
| rel_eval_proposal | 3 | 2 |
| rel_child_parent | 3 | 3 |
| schema_violation_1 | 3 | 3 |
| schema_violation_2 | 3 | 3 |
| classify_file_py | 3 | 2 |
| classify_file_md | 3 | 2 |
| classify_priority_high | 3 | 3 |
| classify_priority_low | 3 | 3 |
| classify_risk_high | 3 | 3 |
| classify_risk_low | 3 | 3 |

## 4. Failure-stage breakdown

| Stage | Count |
|---|---:|
| none | 59 |
| semantic_diff | 5 |
| sandbox | 3 |
| static_analysis | 2 |

## 5. Failure cases

| Goal | Trial | Stage | Notes |
|---|---:|---|---|
| file_summary_1 | 1 | semantic_diff | Semantic diff mismatch. |
| url_extract_1 | 0 | sandbox | `source_execution_error: name 'next' is not defined`. |
| url_extract_1 | 1 | sandbox | `source_execution_error: name 'next' is not defined`. |
| url_extract_1 | 2 | static_analysis | Unterminated string literal (line 3). |
| rel_summary_source | 0 | semantic_diff | Semantic diff mismatch. |
| rel_summary_source | 1 | semantic_diff | Semantic diff mismatch. |
| rel_summary_source | 2 | semantic_diff | Semantic diff mismatch. |
| rel_eval_proposal | 0 | semantic_diff | Semantic diff mismatch. |
| classify_file_py | 2 | static_analysis | Unexpected character after line continuation (line 4). |
| classify_file_md | 2 | sandbox | `source_execution_error: object type not allowed`. |

## 6. Interpretation for paper

Safe interpretation: A 23-goal, 69-trial local live LLM matrix with gpt-4o-mini produced 59/69 full lifecycle successes. All 69 attempts parsed; all failures were caught before authority transfer except the successful promoted cases, and no promotion/matching/nonmatching/disable failures occurred. This supports bounded lifecycle feasibility and failure-stage observability.

## 7. Non-claims

- Not broad LLM reliability.
- Not open-ended recursive self-improvement.
- Not full Python sandbox security.
- Not secure arbitrary code execution.
- Not a broad task-performance benchmark.
- Local run may vary across time/model/API behavior.

## 8. Next step recommendation

Update `docs/paper_outline.md` and future paper result sections to use this 23-goal/69-trial matrix snapshot as the primary live-run result, while retaining bounded-corpus caveats.
