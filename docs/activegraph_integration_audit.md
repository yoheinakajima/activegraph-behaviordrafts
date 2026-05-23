# ActiveGraph Integration Audit (2026-05-23)

## Executive summary

- **Finding:** the repository currently runs experiments on a **local stand-in runtime** (`EventSourcedRuntime`) rather than the real `activegraph` runtime.
- **Status:** **Strategy D (Cannot integrate yet)** for this environment, because `activegraph` is not importable and GitHub access to inspect upstream APIs was blocked (HTTP 403 tunnel error).
- **Impact:** current paper framing must not claim these are ActiveGraph-backed results.

## 1) Local runtime modules and stand-ins

Primary local substrate:
- `src/behaviordrafts/runtime.py` (`EventSourcedRuntime`, `BoundBehavior`)
- `src/behaviordrafts/graph.py` (`GraphState`, local structural diff)
- `src/behaviordrafts/events.py` (`Event`)

Local lifecycle plumbing built on that substrate:
- `src/behaviordrafts/sandbox.py`
- `src/behaviordrafts/promotion.py`
- `src/behaviordrafts/harness.py`
- `src/behaviordrafts/adversarial.py`

Entry points using local substrate:
- `scripts/run_all.py`
- `scripts/run_adversarial.py`
- `scripts/run_live_llm.py`
- `scripts/run_live_llm_matrix.py`

## 2) Duplicated ActiveGraph-like concepts

Local code duplicates expected ActiveGraph-style primitives:
- Event log append/replay-like behavior (`runtime.events`, `apply_event`) 
- Graph projection (`GraphState.objects/relations`)
- Behavior registration/binding (`runtime.behaviors`, `behavior.bound` event)
- Fork/sandbox (`runtime.fork()`)
- Structural diff (`GraphState.structural_diff`)
- Promotion/disable (`promote_behavior`, `disable_behavior`)

## 3) Experimental claims that depend on real ActiveGraph

Claims requiring real ActiveGraph backing:
- “BehaviorDrafts on ActiveGraph”
- ActiveGraph event log / projection semantics
- ActiveGraph behavior binding and runtime execution semantics
- ActiveGraph fork/sandbox semantics (or explicit adapter)
- ActiveGraph-native replay/audit guarantees

## 4) Invalidated / weakened claims under current code

- Any direct claim that experiments are executed on ActiveGraph is **currently invalid**.
- Current results are valid only as **local prototype/runtime-shim evidence** for the BehaviorDraft lifecycle.

## 5) Immediately replaceable components

Pending API availability, likely replaceable first:
- runtime/event/graph substrate (`runtime.py`, `graph.py`, `events.py`) via adapter or direct integration.

## 6) Components likely needing adapters/shims

Potential adapter areas (if ActiveGraph API shape differs):
- sandbox callable wiring (`behavior(event, graph, ctx)` compatibility)
- structural diff normalization to current semantic checks
- promotion metadata shape expected by existing reports

## 7) Minimum honest integration plan

1. Add hard probe for `activegraph` availability and fail-closed mode when ActiveGraph is required.
2. Replace local runtime path with `ActiveGraphAdapter` once upstream APIs are available/inspectable.
3. Keep any unavoidable shim explicitly documented.
4. Re-run deterministic + adversarial + tests and relabel all tables as post-integration.

## ActiveGraph API inspection notes

Attempted:
- `importlib.util.find_spec('activegraph')` → **None**
- `git clone https://github.com/yoheinakajima/activegraph.git` → **failed (403 CONNECT tunnel)**

Because upstream package/repo APIs could not be inspected in this environment, direct integration is currently blocked.
