import time
import uuid
from dataclasses import dataclass
from types import MappingProxyType
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


class EmitOnlyBehaviorContext:
    __slots__ = ("_events", "_budgets", "_allowed_object_types", "_allowed_relation_types", "_metadata")

    def __init__(
        self,
        budgets: Dict[str, Any],
        allowed_object_types: set[str],
        allowed_relation_types: set[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._events: List[Event] = []
        self._budgets = budgets
        self._allowed_object_types = allowed_object_types
        self._allowed_relation_types = allowed_relation_types
        self._metadata = dict(metadata or {})

    def __getattribute__(self, name: str):
        if name == "__dict__":
            raise AttributeError("context internals are not accessible")
        return object.__getattribute__(self, name)

    def _with_metadata(self, payload: Dict[str, Any], entity_key: str) -> Dict[str, Any]:
        out = dict(payload)
        meta = dict(self._metadata)
        if entity_key in out and isinstance(out[entity_key], dict):
            entity = dict(out[entity_key])
            existing_meta = entity.get("provenance") if isinstance(entity.get("provenance"), dict) else {}
            entity["provenance"] = {**existing_meta, **meta}
            out[entity_key] = entity
        return out

    def emit_object_created(self, obj: Dict[str, Any]) -> None:
        if self._allowed_object_types and obj.get("type") not in self._allowed_object_types:
            raise ValueError("object type not allowed")
        self._events.append(Event("object.created", self._with_metadata({"object": obj}, "object")))
        self._enforce_event_budget()

    def emit_relation_created(self, relation: Dict[str, Any]) -> None:
        if self._allowed_relation_types and relation.get("type") not in self._allowed_relation_types:
            raise ValueError("relation type not allowed")
        self._events.append(Event("relation.created", self._with_metadata({"relation": relation}, "relation")))
        self._enforce_event_budget()

    def events(self) -> List[Event]:
        return list(self._events)

    def _enforce_event_budget(self) -> None:
        if len(self._events) > self._budgets.get("max_emitted_events", 10):
            raise ValueError("max emitted events budget exceeded")


class ReadOnlyGraphView:
    def __init__(self, graph):
        self._graph = graph

    def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        obj = self._graph.objects.get(object_id)
        return dict(obj) if obj else None

    def objects_by_type(self, object_type: str) -> List[Dict[str, Any]]:
        return [dict(obj) for obj in self._graph.objects.values() if obj.get("type") == object_type]

    def relations_by_type(self, relation_type: str) -> List[Dict[str, Any]]:
        return [dict(rel) for rel in self._graph.relations if rel.get("type") == relation_type]

    def find_relations(self, from_id: Optional[str] = None, to_id: Optional[str] = None, type: Optional[str] = None) -> List[Dict[str, Any]]:
        out = []
        for rel in self._graph.relations:
            if from_id is not None and rel.get("from") != from_id:
                continue
            if to_id is not None and rel.get("to") != to_id:
                continue
            if type is not None and rel.get("type") != type:
                continue
            out.append(dict(rel))
        return out

    def object_count(self) -> int:
        return len(self._graph.objects)

    def relation_count(self) -> int:
        return len(self._graph.relations)

    @property
    def objects(self):
        return MappingProxyType({k: MappingProxyType(dict(v)) for k, v in self._graph.objects.items()})

    @property
    def relations(self):
        return tuple(MappingProxyType(dict(r)) for r in self._graph.relations)


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

    def runtime_behavior(event, graph, metadata: Optional[Dict[str, Any]] = None):
        ctx = EmitOnlyBehaviorContext({}, set(), set(), metadata=metadata)
        behavior(event.payload, ReadOnlyGraphView(graph), ctx)
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
        ctx = EmitOnlyBehaviorContext(
            budgets=budgets,
            allowed_object_types=set(tests[0].expected_objects) if tests else set(),
            allowed_relation_types=set(tests[0].expected_relations) if tests else set(),
        )
        selected_behavior(trigger_event.payload, ReadOnlyGraphView(fork.graph), ctx)
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
