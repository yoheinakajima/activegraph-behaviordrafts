from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.events import Event
from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests
from behaviordrafts.sandbox import run_behavior_sandbox
from behaviordrafts.demo_behaviors import file_summary_behavior


def test_sandbox_emits_diff():
    goal = {"description":"x","source_code":"def behavior(event, graph):\n return []","scope":{"object_type":"File"},"expected_diff":{"objects_created":1},"goal_name":"file_summary_behavior","fixture_events":[],"expected_events":[],"budgets":{"max_emitted_events":5}}
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    s = run_behavior_sandbox(EventSourcedRuntime(), d, file_summary_behavior, Event("object.created", {"object":{"id":"1","type":"File","content":"A."}}), t, {"max_emitted_events":5,"max_objects_created":3,"max_relations_created":3,"max_runtime_seconds":2})
    assert s.sandbox_passed
