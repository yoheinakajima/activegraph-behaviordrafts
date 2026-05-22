from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .events import Event
from .graph import GraphState

BehaviorFn = Callable[[Event, GraphState, Dict[str, Any]], List[Event]]


@dataclass
class BoundBehavior:
    id: str
    draft_id: str
    behavior_name: str
    on_event_type: str
    scope: Dict[str, Any]
    budgets: Dict[str, Any]
    enabled: bool = True
    fn: BehaviorFn | None = None


@dataclass
class EventSourcedRuntime:
    events: List[Event] = field(default_factory=list)
    graph: GraphState = field(default_factory=GraphState)
    behaviors: Dict[str, BoundBehavior] = field(default_factory=dict)

    def apply_event(self, event: Event) -> None:
        self.events.append(event)
        if event.event_type == "object.created":
            obj = event.payload["object"]
            self.graph.objects[obj["id"]] = obj
        elif event.event_type == "relation.created":
            self.graph.relations.append(event.payload["relation"])
        elif event.event_type == "behavior.disabled":
            bid = event.payload["behavior_binding_id"]
            if bid in self.behaviors:
                self.behaviors[bid].enabled = False

    def emit(self, event: Event) -> None:
        self.apply_event(event)
        self._run_behaviors_for_event(event)

    def _scope_match(self, behavior: BoundBehavior, event: Event) -> bool:
        if event.event_type != behavior.on_event_type:
            return False
        target = behavior.scope.get("object_type")
        if not target:
            return True
        obj = event.payload.get("object", {})
        return obj.get("type") == target

    def _run_behaviors_for_event(self, event: Event) -> None:
        for behavior in self.behaviors.values():
            if not behavior.enabled or behavior.fn is None:
                continue
            if self._scope_match(behavior, event):
                metadata = {
                    "emitted_by": "promoted_behavior",
                    "source_draft_id": behavior.draft_id,
                    "behavior_binding_id": behavior.id,
                    "triggering_event_id": event.id,
                    "triggering_event_type": event.event_type,
                }
                for out_event in behavior.fn(event, self.graph, metadata):
                    self.apply_event(out_event)

    def fork(self) -> "EventSourcedRuntime":
        clone = EventSourcedRuntime()
        clone.events = list(self.events)
        clone.graph = self.graph.clone()
        clone.behaviors = {k: BoundBehavior(**{**vars(v)}) for k, v in self.behaviors.items()}
        return clone
