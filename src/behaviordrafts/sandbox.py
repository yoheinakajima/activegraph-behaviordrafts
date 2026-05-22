import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from .runtime import EventSourcedRuntime


@dataclass
class SandboxRun:
    id: str
    draft_id: str
    fork_id: str
    tests_run: int
    tests_passed: int
    events_emitted: int
    objects_created: int
    relations_created: int
    structural_diff: Dict[str, Any]
    exceptions: List[str]
    budget_used: Dict[str, Any]
    sandbox_passed: bool


def run_behavior_sandbox(runtime: EventSourcedRuntime, draft, behavior_fn, trigger_event, tests, budgets):
    start = time.time()
    fork = runtime.fork()
    before = fork.graph.clone()
    exceptions = []
    try:
        out_events = behavior_fn(trigger_event, fork.graph)
        for ev in out_events:
            fork.apply_event(ev)
    except Exception as e:
        out_events = []
        exceptions.append(str(e))
    diff = fork.graph.structural_diff(before)
    events_emitted = len(out_events)
    budget_ok = (
        events_emitted <= budgets.get("max_emitted_events", 10)
        and diff["objects_created"] <= budgets.get("max_objects_created", 10)
        and diff["relations_created"] <= budgets.get("max_relations_created", 10)
        and (time.time() - start) <= budgets.get("max_runtime_seconds", 2)
    )
    tests_passed = 0
    for t in tests:
        if diff["objects_created"] >= t.expected_diff.get("objects_created", 0):
            tests_passed += 1
    return SandboxRun(str(uuid.uuid4()), draft.id, str(uuid.uuid4()), len(tests), tests_passed,
                      events_emitted, diff["objects_created"], diff["relations_created"], diff,
                      exceptions, {"runtime_seconds": time.time() - start}, budget_ok and not exceptions)
