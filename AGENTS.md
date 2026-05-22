# Repository guidance for Codex sessions

## Deterministic baseline and execution policy

- Preserve deterministic no-key execution.
- Do not start LLM authoring unless explicitly asked.

## Condition semantics (must remain stable)

- **A**: no draft/sandbox/promotion/fire.
- **B**: draft/sandbox allowed but no promotion/live behavior.
- **C**: gated promotion, matching fire, nonmatching silence, disable silence.

## Semantic diff validation (must remain stable)

- **File summary** requires:
  - correct `Summary` object,
  - line count,
  - first sentence,
  - `summarizes` relation.
- **Provenance auditor** requires:
  - `Evaluation` object,
  - missing provenance count,
  - pass/fail,
  - source `PatchProposal` linkage.

## Results artifacts

- Do not commit generated result artifacts:
  - `results/*.json`
  - `results/*.jsonl`
  - `results/*.md`
- Keep `results/.gitkeep`.
- Treat generated summaries as reproducible outputs, not source.

## Required verification before completion

Run all of the following before reporting completion:

```bash
python scripts/clean_results.py
python scripts/run_all.py
PYTHONPATH=src pytest -q
```
