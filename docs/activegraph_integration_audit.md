# ActiveGraph Integration Audit (2026-05-23)

## Status

BehaviorDrafts now uses an **ActiveGraph-backed adapter** (`ActiveGraphAdapter`) as the default backend selection (`BEHAVIORDRAFTS_BACKEND=activegraph_adapter`).

## Native ActiveGraph primitives now instantiated

- `activegraph.Graph`
- `activegraph.Runtime`
- `activegraph.Event`
- `activegraph.Behavior` (registration path via adapter runtime rebuild)

## Adapter glue still present

- Dynamic behavior registration is implemented via adapter-managed registry + runtime rebuild (`adapter_glue`).
- Disable/unbind remains adapter metadata driven (`adapter_glue`).
- Diff normalization to repository semantic-diff shape remains adapter normalization (`adapter_glue`).
- Sandbox pre-parent-event fork fallback is documented as `local_shim_required:fork_without_parent_event`.

## Claim framing (post-integration)

Use: **"BehaviorDrafts on an ActiveGraph-backed adapter with documented shims."**

Do not claim fully pure/native ActiveGraph behavior lifecycle until dynamic bind/unbind and all sandbox fork points are native without adapter-managed fallback.
