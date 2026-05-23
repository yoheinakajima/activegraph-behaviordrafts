# Local Live LLM Run Workflow

Live LLM runs are local/manual because this Codex environment does not expose `OPENAI_API_KEY`. Deterministic baseline scripts remain no-key and do not call a live model by default.

Set environment locally:

    export OPENAI_API_KEY="..."
    export BEHAVIORDRAFTS_MODEL="gpt-4o-mini"

Run full workflow:

    python scripts/clean_results.py
    python scripts/run_all.py
    python scripts/run_adversarial.py
    python scripts/run_live_llm.py
    python scripts/generate_paper_tables.py
    PYTHONPATH=src pytest -q

Expected live outputs:

- `results/live_llm_summary.json`
- `results/live_llm_summary.md`
- `results/live_llm_cases.jsonl`
- `results/live_llm_prompts.jsonl`
- `results/live_llm_raw_responses.jsonl`

For paper tables, copy metrics from `results/live_llm_summary.json` and Table 5 from `results/paper_tables.md`.

Do not commit generated artifacts under `results/*.json`, `results/*.jsonl`, or `results/*.md`; keep only `results/.gitkeep` tracked.

`run_live_llm.py` exits with code `2` when `OPENAI_API_KEY` is missing and prints a clear skip message.
