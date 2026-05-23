# ActiveGraph Integration Audit (2026-05-23)

## Status

BehaviorDrafts now runs on an **ActiveGraph-backed adapter** (`ActiveGraphAdapter`) as the default backend path (`BEHAVIORDRAFTS_BACKEND=activegraph_adapter`).

ActiveGraph imports locally (`import activegraph` succeeds in this environment), and both deterministic/adversarial checks and the live LLM matrix have now been rerun on the `activegraph_adapter` path.

## Native ActiveGraph primitives in use

- `activegraph.Graph`
- `activegraph.Runtime`
- `activegraph.Event`
- `activegraph.Behavior`
- `Graph.add_object`
- `Graph.add_relation`
- `Graph.emit`
- `Runtime.fork`
- `Runtime.diff`

## ActiveGraphAdapter-backed results framing

Results should be framed as:

- **ActiveGraphAdapter-backed** (real ActiveGraph primitives where available)
- **Not pure/native ActiveGraph end-to-end** (adapter glue remains in lifecycle wiring)

Recommended wording:

> BehaviorDrafts on an ActiveGraph-backed adapter with documented shims.

## Remaining adapter shims (explicit)

- `behavior_dispatch_adapter`
- `dynamic_behavior_registration_adapter`
- `disable_metadata_adapter`
- `diff_normalization_adapter`
- `snapshot_diff_adapter`

## Post-ActiveGraphAdapter rerun context

- Deterministic lifecycle runs: 6
- Adversarial cases: 29
- Cases matching expectation: 29
- Unexpected passes: 0
- Unexpected failures: 0
- Promotions succeeded: 2
- Live graph violations: 0
- Tests: 76 passed
- Live matrix (`gpt-4o-mini`): 23 goals × 3 trials = 69 total, 60 full lifecycle successes
