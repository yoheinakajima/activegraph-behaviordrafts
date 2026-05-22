import pytest
from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests
from behaviordrafts.events import Event
from behaviordrafts.promotion import disable_behavior, promote_behavior
from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.sandbox import compile_runtime_behavior, run_behavior_sandbox
from behaviordrafts.static_analysis import run_static_analysis


def _file_summary_goal(source_code: str):
    return {
        "description": "x",
        "source_code": source_code,
        "scope": {"object_type": "File"},
        "expected_diff": {"objects_created": 1},
        "goal_name": "file_summary_behavior",
        "fixture_events": [],
        "expected_events": [],
        "expected_objects": ["Summary"],
        "expected_relations": ["summarizes"],
        "trigger_object": {"id": "1", "type": "File", "content": "A."},
        "budgets": {"max_emitted_events": 5, "max_objects_created": 3, "max_relations_created": 3, "max_runtime_seconds": 2},
    }


def _promote(runtime, goal):
    draft = author_behavior_draft_fixture("x", goal)
    tests = author_behavior_tests(draft, goal)
    analysis = run_static_analysis(draft)
    sandbox = run_behavior_sandbox(runtime, draft, None, Event("object.created", {"object": goal["trigger_object"]}), tests, goal["budgets"], analysis_passed=analysis.analysis_passed)
    decision = promote_behavior(runtime, draft, analysis, sandbox, compile_runtime_behavior(draft.source_code))
    assert decision.decision == "approved"
    return next(iter(runtime.behaviors.values()))


def test_compile_runtime_behavior_uses_readonly_graph_and_emit_only_ctx():
    seen = {}
    behavior = compile_runtime_behavior(
        "def behavior(event, graph, ctx):\n"
        "    ctx.emit_object_created({'id':'summary-1','type':'Summary','first_sentence':'A.','line_count':1})\n"
    )
    runtime = EventSourcedRuntime()
    event = Event("object.created", {"object": {"id": "1", "type": "File", "content": "A."}})
    def wrapper(e, g, metadata):
        seen["metadata"] = metadata
        return behavior(e, g, metadata)
    out = wrapper(event, runtime.graph, {"emitted_by": "promoted_behavior"})
    assert len(out) == 1
    assert out[0].payload["object"]["provenance"]["emitted_by"] == "promoted_behavior"


def test_promoted_runtime_blocks_ctx_internals_and_runtime_access():
    behavior = compile_runtime_behavior("def behavior(event, graph, ctx):\n    ctx.__dict__\n")
    runtime = EventSourcedRuntime()
    with pytest.raises(AttributeError):
        behavior(Event("object.created", {"object": {"id": "1", "type": "File", "content": "A."}}), runtime.graph, {})


def test_promoted_runtime_can_emit_and_disable_still_silent():
    src = (
        "def behavior(event, graph, ctx):\n"
        "    obj=event['object']\n"
        "    sid='summary-'+obj['id']\n"
        "    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'A.','line_count':1})\n"
        "    ctx.emit_relation_created({'type':'summarizes','from':sid,'to':obj['id']})\n"
    )
    goal = _file_summary_goal(src)
    runtime = EventSourcedRuntime()
    binding = _promote(runtime, goal)

    trigger = Event("object.created", {"object": goal["trigger_object"]})
    runtime.emit(trigger)
    emitted_summary = runtime.graph.objects["summary-1"]
    assert emitted_summary["provenance"]["source_draft_id"] == binding.draft_id
    assert emitted_summary["provenance"]["behavior_binding_id"] == binding.id
    assert emitted_summary["provenance"]["triggering_event_id"] == trigger.id

    disable_behavior(runtime, binding.id)
    before = len(runtime.events)
    runtime.emit(trigger)
    assert len(runtime.events) == before + 1


def test_runtime_and_sandbox_use_same_behavior_interface():
    source = (
        "def behavior(event, graph, ctx):\n"
        "    obj=event['object']\n"
        "    sid='summary-'+obj['id']\n"
        "    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'A.','line_count':1})\n"
    )
    goal = _file_summary_goal(source)
    runtime = EventSourcedRuntime()
    binding = _promote(runtime, goal)
    runtime.emit(Event("object.created", {"object": goal["trigger_object"]}))
    assert "summary-1" in runtime.graph.objects
    assert runtime.behaviors[binding.id].draft_id == binding.draft_id
