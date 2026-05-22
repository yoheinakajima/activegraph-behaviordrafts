import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .events import Event
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
    source_execution_mode: str
    source_compiled: bool
    source_execution_error: Optional[str]
    sandbox_executed_generated_source: bool


class SandboxContext:
    def __init__(self, budgets: Dict[str, Any], allowed_object_types: set[str], allowed_relation_types: set[str]):
        self._events: List[Event] = []
        self._budgets = budgets
        self._allowed_object_types = allowed_object_types
        self._allowed_relation_types = allowed_relation_types

    def emit_object_created(self, obj: Dict[str, Any]) -> None:
        if self._allowed_object_types and obj.get("type") not in self._allowed_object_types:
            raise ValueError("object type not allowed")
        self._events.append(Event("object.created", {"object": obj}))
        self._enforce_event_budget()

    def emit_relation_created(self, relation: Dict[str, Any]) -> None:
        if self._allowed_relation_types and relation.get("type") not in self._allowed_relation_types:
            raise ValueError("relation type not allowed")
        self._events.append(Event("relation.created", {"relation": relation}))
        self._enforce_event_budget()

    def events(self) -> List[Event]:
        return list(self._events)

    def _enforce_event_budget(self) -> None:
        if len(self._events) > self._budgets.get("max_emitted_events", 10):
            raise ValueError("max emitted events budget exceeded")


def _compile_behavior_source(source_code: str):
    safe_builtins = {"len": len, "sum": sum, "min": min, "max": max, "any": any, "all": all, "range": range}
    namespace: Dict[str, Any] = {"__builtins__": safe_builtins}
    code = compile(source_code, "<draft_source>", "exec")
    exec(code, namespace, namespace)
    behavior = namespace.get("behavior")
    if not callable(behavior):
        raise ValueError("source must define callable `behavior(event, graph, ctx)`")
    return behavior


def compile_runtime_behavior(source_code: str):
    behavior = _compile_behavior_source(source_code)

    def runtime_behavior(event, graph):
        ctx = SandboxContext({}, set(), set())
        behavior(event.payload, graph, ctx)
        return ctx.events()

    return runtime_behavior


def run_behavior_sandbox(runtime: EventSourcedRuntime, draft, behavior_fn, trigger_event, tests, budgets, analysis_passed: bool = True):
    start = time.time()
    fork = runtime.fork()
    before = fork.graph.clone()
    exceptions = []
    source_compiled = False
    source_error = None
    source_execution_mode = "fixture_function"
    sandbox_executed_generated_source = False
    try:
        selected_behavior = behavior_fn
        if analysis_passed:
            selected_behavior = _compile_behavior_source(draft.source_code)
            source_compiled = True
            source_execution_mode = "draft_source"
            sandbox_executed_generated_source = True
        ctx = SandboxContext(
            budgets=budgets,
            allowed_object_types=set(tests[0].expected_objects) if tests else set(),
            allowed_relation_types=set(tests[0].expected_relations) if tests else set(),
        )
        selected_behavior(trigger_event.payload, fork.graph, ctx)
        out_events = ctx.events()
        for ev in out_events:
            fork.apply_event(ev)
    except Exception as e:
        out_events = []
        source_error = str(e)
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
                      exceptions, {"runtime_seconds": time.time() - start}, budget_ok and not exceptions,
                      source_execution_mode, source_compiled, source_error, sandbox_executed_generated_source)
