from dataclasses import dataclass
import uuid

from .runtime import BoundBehavior
from .events import Event


@dataclass
class PromotionDecision:
    id: str
    draft_id: str
    decision: str
    reason: str
    scope: dict
    budgets: dict
    approved_by: str
    promotion_event_id: str | None


def promote_behavior(
    runtime,
    draft,
    analysis,
    sandbox_run,
    behavior_fn,
    approval_policy=True,
    bind_event_type=None,
    bind_scope=None,
):
    if not (analysis.analysis_passed and sandbox_run.sandbox_passed and sandbox_run.tests_passed == sandbox_run.tests_run and approval_policy):
        return PromotionDecision(str(uuid.uuid4()), draft.id, "rejected", "gates not met", draft.declared_scope, {}, "policy", None)
    binding_id = str(uuid.uuid4())
    on_event_type = bind_event_type or draft.declared_trigger_events[0]
    scope = bind_scope or draft.declared_scope
    runtime.behaviors[binding_id] = BoundBehavior(
        binding_id,
        draft.id,
        draft.name,
        on_event_type,
        scope,
        {"max_emitted_events": 10},
        True,
        behavior_fn,
    )
    ev = Event("behavior.bound", {"binding_id": binding_id, "draft_id": draft.id})
    runtime.apply_event(ev)
    return PromotionDecision(str(uuid.uuid4()), draft.id, "approved", "all gates passed", scope, {"max_emitted_events": 10}, "policy", ev.id)


def disable_behavior(runtime, binding_id):
    runtime.emit(Event("behavior.disabled", {"behavior_binding_id": binding_id}))
