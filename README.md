# Code Without Authority

Event-sourced behavior drafts for LLM self-modification.

## Overview

`activegraph-behaviordrafts` is an experimental Python repo that demonstrates a controlled lifecycle for LLM-authored behavior code:

1. Author an inert `BehaviorDraft` artifact in the event log.
2. Run static analysis and draft tests.
3. Execute draft behavior only in a sandbox fork.
4. Inspect structural diff and policy checks.
5. Promote via explicit logged decision into an active `BehaviorBinding`.
6. Disable with a forward-only event.

This repo intentionally avoids claims of open-ended recursive self-improvement. It focuses on the next controlled tier after graph-native self-change.

## Reproducibility

```bash
pip install -r requirements.txt
python scripts/run_all.py
```

Optional LLM path (non-default):

```bash
python scripts/run_all.py --llm
```

Default execution is deterministic and requires no API key.
