from behaviordrafts.drafts import BehaviorDraft
from behaviordrafts.events import Event
from behaviordrafts.promotion import disable_behavior, promote_behavior
from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.sandbox import compile_runtime_behavior


class _Analysis:
    analysis_passed = True


class _Sandbox:
    sandbox_passed = True
    tests_passed = 1
    tests_run = 1


def _draft(trigger_events):
    return BehaviorDraft(
        id="d1",
        name="heading_count",
        description="x",
        source_code=(
            "def behavior(event, graph, ctx):\n"
            "    obj = event['object']\n"
            "    ctx.emit_object_created({'id': f\"heading-{obj['id']}\", 'type': 'HeadingCount', 'count': 1, 'file_id': obj['id']})\n"
        ),
        declared_trigger_events=trigger_events,
        declared_scope={"object_type": "WrongType"},
        declared_inputs=["event", "graph"],
        declared_outputs=["events"],
        declared_permissions=["emit.object.created"],
        declared_dependencies=[],
        expected_emitted_events=["object.created"],
        expected_graph_mutations={"objects_created": 1, "relations_created": 0},
        created_by="fixture",
        created_from_goal="heading_count_1",
        model_used="none",
        prompt_hash="none",
        authoring_mode="fixture",
        provenance={},
        status="drafted",
    )


def _matching_event_fired(runtime, trigger, allowed_object_types, allowed_relation_types):
    before_objects = set(runtime.graph.objects.keys())
    before_relations = len(runtime.graph.relations)
    before_events = len(runtime.events)
    runtime.emit(trigger)
    created_object_ids = set(runtime.graph.objects.keys()) - before_objects
    created_allowed_objects = any(runtime.graph.objects[o].get("type") in set(allowed_object_types) for o in created_object_ids)
    created_allowed_relations = any(r.get("type") in set(allowed_relation_types) for r in runtime.graph.relations[before_relations:])
    emitted_event_delta = len(runtime.events) - before_events
    return (created_allowed_objects or created_allowed_relations) and emitted_event_delta > 1


def test_promoted_behavior_fires_on_equivalent_matching_event_and_disable_stops_future_firing():
    runtime = EventSourcedRuntime()
    draft = _draft(["File.Created"])
    trigger_object = {"id": "f1", "type": "File", "content": "# x"}
    trigger = Event("object.created", {"object": trigger_object})

    decision = promote_behavior(
        runtime,
        draft,
        _Analysis(),
        _Sandbox(),
        compile_runtime_behavior(draft.source_code),
        bind_event_type="object.created",
        bind_scope={"object_type": "File"},
    )
    assert decision.decision == "approved"
    binding_id = next(iter(runtime.behaviors))

    assert _matching_event_fired(runtime, trigger, ["HeadingCount"], [])

    before = len(runtime.events)
    runtime.emit(Event("object.created", {"object": {"id": "u1", "type": "Unrelated"}}))
    assert len(runtime.events) == before + 1

    disable_behavior(runtime, binding_id)
    before_disabled = len(runtime.events)
    runtime.emit(trigger)
    assert len(runtime.events) == before_disabled + 1


def test_matching_fire_detection_uses_emitted_delta_not_preexisting_object_count():
    runtime = EventSourcedRuntime()
    runtime.graph.objects["pre1"] = {"id": "pre1", "type": "HeadingCount"}
    trigger = Event("object.created", {"object": {"id": "f2", "type": "Unrelated", "content": "no headers"}})

    fired = _matching_event_fired(runtime, trigger, ["HeadingCount"], [])
    assert not fired
