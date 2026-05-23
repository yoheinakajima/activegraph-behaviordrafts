from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests
from behaviordrafts.events import Event
from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.sandbox import run_behavior_sandbox
from behaviordrafts.static_analysis import run_static_analysis


def test_matrix_goal_constructs_tests_and_reaches_sandbox():
    goal = {
        "goal_id": "g-matrix",
        "description": "matrix",
        "source_code": "def behavior(event, graph, ctx):\n    pass\n",
        "scope": {"object_type": "File"},
        "trigger_object": {"id": "f1", "type": "File", "content": "A"},
        "expected_objects": [],
        "expected_relations": [],
        "expected_diff": {"objects_created": 0, "relations_created": 0},
        "semantic_validator_type": "summary_validator",
        "budgets": {"max_emitted_events": 3},
    }
    draft = author_behavior_draft_fixture("matrix", goal)
    analysis = run_static_analysis(draft)
    tests = author_behavior_tests(draft, goal)
    sandbox = run_behavior_sandbox(
        EventSourcedRuntime(),
        draft,
        None,
        Event("object.created", {"object": goal["trigger_object"]}),
        tests,
        goal["budgets"],
        analysis_passed=analysis.analysis_passed,
    )
    assert tests[0].fixture_events == []
    assert sandbox is not None
