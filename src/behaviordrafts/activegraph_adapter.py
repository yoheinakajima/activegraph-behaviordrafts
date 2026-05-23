from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .events import Event
from .runtime import BoundBehavior, EventSourcedRuntime
from .activegraph_backend import probe_activegraph


@dataclass
class ActiveGraphAdapter:
    """Adapter facade for experiment runtime operations.

    Methods are tagged in ``capabilities`` as one of:
    - native_activegraph
    - adapter_glue
    - local_shim_required
    """

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
        self.backend_details = {"probe_backend": probe.module, "probe_message": probe.reason}
        # Current integration is API-probed and explicit; runtime ops still shim-backed until package is importable.
        self._shim = EventSourcedRuntime()
        if self.activegraph_available:
            self.activegraph_native_features.extend(["import_probe"])
        else:
            if not self.allow_local_shim:
                raise RuntimeError(
                    "ActiveGraphAdapter requires activegraph, or explicit allow_local_shim=True for documented shim mode"
                )
            self.adapter_shim_features.extend([
                "create_runtime_graph",
                "emit",
                "read_state",
                "run_behavior",
                "fork",
                "diff",
                "bind_behavior",
                "disable_behavior",
            ])

        self.capabilities = {
            "create_runtime_graph": "local_shim_required",
            "emit": "local_shim_required",
            "read_state": "adapter_glue",
            "run_behavior": "local_shim_required",
            "fork": "local_shim_required",
            "diff": "adapter_glue",
            "bind_behavior": "local_shim_required",
            "disable_behavior": "local_shim_required",
        }

    @property
    def runtime(self) -> EventSourcedRuntime:
        return self._shim

    def __getattr__(self, name: str) -> Any:
        return getattr(self._shim, name)

    def emit(self, event: Event) -> None:
        self._shim.emit(event)

    def read_state(self) -> Dict[str, Any]:
        return {"objects": self._shim.graph.objects, "relations": self._shim.graph.relations}

    def fork(self) -> "ActiveGraphAdapter":
        child = ActiveGraphAdapter(allow_local_shim=True)
        child._shim = self._shim.fork()
        return child

    def diff(self, parent: "ActiveGraphAdapter") -> Dict[str, Any]:
        return self._shim.graph.structural_diff(parent._shim.graph)

    def bind_behavior(self, behavior: BoundBehavior) -> None:
        self._shim.behaviors[behavior.id] = behavior

    def disable_behavior(self, behavior_binding_id: str) -> None:
        self._shim.apply_event(Event("behavior.disabled", {"behavior_binding_id": behavior_binding_id}))


def make_default_runtime(*, allow_local_shim: bool = False):
    probe = probe_activegraph()
    if probe.available:
        return ActiveGraphAdapter(allow_local_shim=allow_local_shim)
    if allow_local_shim:
        return ActiveGraphAdapter(allow_local_shim=True)
    raise RuntimeError("ActiveGraph unavailable; pass allow_local_shim=True to run explicit local shim mode")
