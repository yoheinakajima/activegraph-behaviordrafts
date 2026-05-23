from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .activegraph_backend import probe_activegraph
from .events import Event
from .graph import GraphState
from .runtime import BoundBehavior, EventSourcedRuntime


@dataclass
class ActiveGraphAdapter:
    allow_local_shim: bool = False
    backend_kind: str = "activegraph_adapter"
    activegraph_available: bool = field(init=False)
    backend_details: Dict[str, Any] = field(init=False)
    activegraph_native_features: List[str] = field(default_factory=list)
    adapter_shim_features: List[str] = field(default_factory=list)
    capabilities: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        probe = probe_activegraph()
        self.activegraph_available = probe.available
        self._event_seq = 0
        self._shim = EventSourcedRuntime()
        self._ag_graph = None
        self._ag_runtime = None
        self._ag_behavior_by_binding: Dict[str, Any] = {}

        if self.activegraph_available:
            import activegraph  # type: ignore

            self._activegraph = activegraph
            self._ag_graph = activegraph.Graph()
            self._ag_runtime = activegraph.Runtime(self._ag_graph, behaviors=[])
            version = getattr(activegraph, "__version__", "unknown")
            self.backend_details = {
                "activegraph_available": True,
                "activegraph_package_version": version,
                "native_primitives_used": ["Graph", "Runtime", "Event", "Behavior"],
            }
            self.activegraph_native_features.extend(["activegraph.Graph", "activegraph.Runtime", "activegraph.Event", "activegraph.Behavior", "Graph.add_object", "Graph.add_relation", "Graph.emit", "Runtime.fork", "Runtime.diff"])
            self.adapter_shim_features.extend(["behavior_dispatch_adapter", "dynamic_behavior_registration_adapter", "disable_metadata_adapter", "diff_normalization_adapter"])
        else:
            if not self.allow_local_shim:
                self.backend_kind = "activegraph_import_probe_local_shim"
            self.backend_details = {"activegraph_available": False, "local_shim_required": True, "probe_message": probe.reason}
            self.adapter_shim_features.extend(["local_shim_runtime", "behavior_dispatch_adapter", "dynamic_behavior_registration_adapter", "disable_metadata_adapter", "diff_normalization_adapter"])

        self.capabilities = {
            "create_runtime_graph": "native_activegraph" if self.activegraph_available else "local_shim_required",
            "emit": "native_activegraph" if self.activegraph_available else "local_shim_required",
            "read_state": "adapter_glue",
            "run_behavior": "adapter_glue",
            "fork": "native_activegraph" if self.activegraph_available else "local_shim_required",
            "diff": "native_activegraph" if self.activegraph_available else "local_shim_required",
            "bind_behavior": "adapter_glue",
            "disable_behavior": "adapter_glue",
        }

    @property
    def runtime(self):
        return self._ag_runtime if self._ag_runtime is not None else self._shim

    @property
    def shim_runtime(self) -> EventSourcedRuntime:
        return self._shim

    @property
    def graph(self):
        return self._ag_graph if self._ag_graph is not None else self._shim.graph

    def __getattr__(self, name: str) -> Any:
        return getattr(self._shim, name)

    @property
    def behaviors(self):
        return self._shim.behaviors

    def _next_event_id(self, event_type: str) -> str:
        self._event_seq += 1
        return f"evt-{event_type}-{self._event_seq:06d}"

    def _to_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        for name in ("to_dict", "model_dump"):
            fn = getattr(value, name, None)
            if callable(fn):
                out = fn()
                if isinstance(out, dict):
                    return out
        out: Dict[str, Any] = {}
        for k in ("id", "type", "data", "source", "target", "from", "to", "payload", "actor", "caused_by"):
            if hasattr(value, k):
                out[k] = getattr(value, k)
        return out

    def add_object(self, type: str, data: Dict[str, Any], actor: str = "system", caused_by: Optional[str] = None):
        if self._ag_graph is not None:
            return self._ag_graph.add_object(type, data, actor=actor, caused_by=caused_by)
        obj_id = data.get("id")
        self._shim.graph.objects[obj_id] = {"id": obj_id, "type": type, **data}
        return self._shim.graph.objects[obj_id]

    def add_relation(self, source: str, target: str, type: str, data: Optional[Dict[str, Any]] = None, actor: str = "system", caused_by: Optional[str] = None):
        if self._ag_graph is not None:
            return self._ag_graph.add_relation(source, target, type, data=data, actor=actor, caused_by=caused_by)
        rel = {"from": source, "to": target, "type": type, **(data or {})}
        self._shim.graph.relations.append(rel)
        return rel

    def emit_event(self, type: str, payload: Dict[str, Any], actor: str = "system", caused_by: Optional[str] = None):
        if self._ag_graph is not None:
            ag_event = self._activegraph.Event(id=self._next_event_id(type), type=type, payload=payload, actor=actor, caused_by=caused_by)
            self._ag_graph.emit(ag_event)
        self.emit(Event(type, payload))

    def emit(self, event: Event) -> None:
        self._shim.emit(event)

    def apply_event(self, event: Event) -> None:
        self._shim.apply_event(event)

    def all_objects(self):
        if self._ag_graph is not None:
            return [self._to_dict(o) for o in self._ag_graph.all_objects()]
        return list(self._shim.graph.objects.values())

    def all_relations(self):
        if self._ag_graph is not None:
            return [self._to_dict(r) for r in self._ag_graph.all_relations()]
        return list(self._shim.graph.relations)

    def objects(self, type: Optional[str] = None):
        if self._ag_graph is not None:
            return [self._to_dict(o) for o in self._ag_graph.objects(type=type)]
        return [o for o in self._shim.graph.objects.values() if type is None or o.get("type") == type]

    def relations(self, type: Optional[str] = None, source: Optional[str] = None, target: Optional[str] = None):
        if self._ag_graph is not None:
            return [self._to_dict(r) for r in self._ag_graph.relations(source=source, target=target, type=type)]
        out = self._shim.graph.relations
        return [r for r in out if (type is None or r.get("type") == type) and (source is None or r.get("from") == source) and (target is None or r.get("to") == target)]

    def get_object(self, id_: str):
        if self._ag_graph is not None:
            return self._to_dict(self._ag_graph.get_object(id_))
        return self._shim.graph.objects.get(id_)

    def get_relation(self, id_: str):
        if self._ag_graph is not None:
            return self._to_dict(self._ag_graph.get_relation(id_))
        for rel in self._shim.graph.relations:
            if rel.get("id") == id_:
                return rel
        return None

    def read_state(self) -> Dict[str, Any]:
        return {"objects": self._shim.graph.objects, "relations": self._shim.graph.relations}

    def fork(self) -> "ActiveGraphAdapter":
        child = ActiveGraphAdapter(allow_local_shim=True)
        child._shim = self._shim.fork()
        if self._ag_runtime is not None:
            if self._shim.events:
                at_event = self._shim.events[-1].id
                child._ag_runtime = self._ag_runtime.fork(at_event=at_event)
                child._ag_graph = child._ag_runtime.graph
            else:
                child.adapter_shim_features.append("local_shim_required:fork_without_parent_event")
                child._ag_graph = self._activegraph.Graph()
                child._ag_runtime = self._activegraph.Runtime(child._ag_graph, behaviors=[])
            child._activegraph = self._activegraph
            child.activegraph_available = True
        return child

    def diff(self, parent: "ActiveGraphAdapter") -> Dict[str, Any]:
        if self._ag_runtime is not None and parent._ag_runtime is not None:
            _ = self._ag_runtime.diff(parent._ag_runtime)
        return self._shim.graph.structural_diff(parent._shim.graph)

    def bind_behavior(self, behavior: BoundBehavior) -> None:
        self._shim.behaviors[behavior.id] = behavior
        if self._ag_runtime is not None and behavior.fn is not None:
            def _ag_fn(ag_event, ag_graph, ag_ctx):
                ev = Event(getattr(ag_event, "type", "event"), getattr(ag_event, "payload", {}), id=getattr(ag_event, "id", "ag"))
                for out in behavior.fn(ev, self._shim.graph, {}):
                    self.apply_event(out)
                return None
            ag_behavior = self._activegraph.Behavior(name=behavior.behavior_name, fn=_ag_fn, on=[behavior.on_event_type])
            self._ag_behavior_by_binding[behavior.id] = ag_behavior
            # adapter_glue: rebuild runtime for dynamic registration
            all_behaviors = list(self._ag_behavior_by_binding.values())
            self._ag_runtime = self._activegraph.Runtime(self._ag_graph, behaviors=all_behaviors)

    def disable_behavior(self, behavior_binding_id: str) -> None:
        self._shim.apply_event(Event("behavior.disabled", {"behavior_binding_id": behavior_binding_id}))


def make_default_runtime(*, allow_local_shim: bool = False):
    return ActiveGraphAdapter(allow_local_shim=allow_local_shim)
