from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.events import Event
from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests
from behaviordrafts.sandbox import run_behavior_sandbox


def test_sandbox_emits_diff():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n ctx.emit_object_created({'id':'summary-1','type':'Summary','first_sentence':'A.','line_count':1})\n ctx.emit_relation_created({'type':'summarizes','from':'summary-1','to':'1'})","scope":{"object_type":"File"},"expected_diff":{"objects_created":1},"goal_name":"file_summary_behavior","fixture_events":[],"expected_events":[],"expected_objects":["Summary"],"expected_relations":["summarizes"],"budgets":{"max_emitted_events":5}}
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    s = run_behavior_sandbox(EventSourcedRuntime(), d, None, Event("object.created", {"object":{"id":"1","type":"File","content":"A."}}), t, {"max_emitted_events":5,"max_objects_created":3,"max_relations_created":3,"max_runtime_seconds":2})
    assert s.sandbox_passed
    assert s.source_compiled
    assert s.sandbox_executed_generated_source


def test_sandbox_does_not_mutate_live_graph():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n ctx.emit_object_created({'id':'summary-1','type':'Summary','first_sentence':'A.','line_count':1})","scope":{"object_type":"File"},"expected_diff":{"objects_created":1},"goal_name":"file_summary_behavior","fixture_events":[],"expected_events":[],"expected_objects":["Summary"],"expected_relations":[],"budgets":{"max_emitted_events":5}}
    runtime = EventSourcedRuntime()
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    run_behavior_sandbox(runtime, d, None, Event("object.created", {"object":{"id":"1","type":"File","content":"A."}}), t, {"max_emitted_events":5,"max_objects_created":3,"max_relations_created":3,"max_runtime_seconds":2})
    assert runtime.graph.objects == {}


def test_sandbox_rejects_direct_graph_mutation_runtime():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n graph.objects['x']={'id':'x','type':'Summary'}","scope":{"object_type":"File"},"expected_diff":{"objects_created":1},"goal_name":"file_summary_behavior","fixture_events":[],"expected_events":[],"expected_objects":["Summary"],"expected_relations":[],"budgets":{"max_emitted_events":5}}
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    s = run_behavior_sandbox(EventSourcedRuntime(), d, None, Event("object.created", {"object":{"id":"1","type":"File","content":"A."}}), t, {"max_emitted_events":5,"max_objects_created":3,"max_relations_created":3,"max_runtime_seconds":2}, analysis_passed=True)
    assert not s.sandbox_passed
    assert s.source_execution_error


def test_sandbox_allows_enumerate_builtin():
    source_code = """def behavior(event, graph, ctx):
    obj = event["object"]
    lines = obj.get("content", "").splitlines()
    for i, line in enumerate(lines):
        if "TODO" in line:
            ctx.emit_object_created({"id": f"todo-{obj['id']}-{i}", "type": "TodoFinding", "content": line})
"""
    goal = {"description":"x","source_code":source_code,"scope":{"object_type":"File"},"expected_diff":{"objects_created":1},"goal_name":"todo_behavior","fixture_events":[],"expected_events":[],"expected_objects":["TodoFinding"],"expected_relations":[],"budgets":{"max_emitted_events":5}}
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    s = run_behavior_sandbox(EventSourcedRuntime(), d, None, Event("object.created", {"object":{"id":"1","type":"File","content":"TODO: x"}}), t, {"max_emitted_events":5,"max_objects_created":3,"max_relations_created":3,"max_runtime_seconds":2}, analysis_passed=True)
    assert s.sandbox_passed
