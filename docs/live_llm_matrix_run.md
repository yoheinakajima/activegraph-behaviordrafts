# Live LLM Matrix Local Run

Run locally with a real key:

```bash
export OPENAI_API_KEY="..."
export BEHAVIORDRAFTS_MODEL="gpt-4o-mini"
python scripts/run_live_llm_matrix.py --trials 3
python scripts/generate_paper_tables.py
```

Cheaper smoke run:

```bash
python scripts/run_live_llm_matrix.py --goal-limit 3 --trials 1
```

Notes:
- Live matrix is optional and never runs in deterministic default test paths.
- Generated matrix artifacts are written under `results/` and are git-ignored.
