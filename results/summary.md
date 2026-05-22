# Behavior Draft Experiment Summary

- **Timestamp (UTC):** 2026-05-22T17:27:47+00:00
- **Goals:** 2
- **Conditions:** 3
- **Total runs:** 6

## Aggregate Metrics

| Metric | Value |
|---|---:|
| Goals | 2 |
| Conditions | 3 |
| Runs | 6 |
| Drafts created | 4 |
| Static analysis passed | 4 |
| Sandbox passed | 4 |
| Promotions succeeded | 2 |

## Condition Results

| Condition | Drafts | Sandbox Runs | Promotions | Matching Fires | Nonmatching Silent |
|---|---:|---:|---:|---:|---:|
| A | 0 | 0 | 0 | 0 | 0 |
| B | 2 | 2 | 0 | 0 | 0 |
| C | 2 | 2 | 2 | 2 | 2 |

## Per-goal Results

| Goal | Runs | Promotions | Sandbox Passed | Diff Match |
|---|---:|---:|---:|---:|
| file_summary_behavior | 3 | 1 | 2 | 2 |
| provenance_auditor_behavior | 3 | 1 | 2 | 2 |

## Interpretation

Condition A cannot author new behavior. Condition B can create inert drafts but cannot change runtime behavior. Condition C can promote scoped behavior after validation, enabling the two demo capabilities while preserving live graph isolation before promotion.
