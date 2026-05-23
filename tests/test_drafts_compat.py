from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests


def _source():
    return "def behavior(event, graph, ctx):\n    pass\n"


def test_author_behavior_tests_supports_original_goal_shape():
    goal = {
        "goal_name": "legacy",
        "description": "legacy",
        "source_code": _source(),
        "scope": {"object_type": "File"},
        "fixture_events": [],
        "expected_events": ["object.created"],
        "expected_objects": ["Summary"],
        "expected_relations": ["summarizes"],
        "expected_diff": {"objects_created": 1, "relations_created": 1},
    }
    draft = author_behavior_draft_fixture("legacy", goal)
    tests = author_behavior_tests(draft, goal)
    assert tests[0].fixture_events == []
    assert tests[0].expected_events == ["object.created"]


def test_author_behavior_tests_supports_matrix_goal_shape_defaults():
    goal = {
        "goal_id": "matrix-1",
        "description": "matrix",
        "source_code": _source(),
        "scope": {"object_type": "File"},
        "trigger_object": {"id": "f1", "type": "File", "content": "A"},
        "expected_objects": ["Summary"],
        "expected_relations": ["summarizes"],
        "expected_diff": {"objects_created": 1, "relations_created": 1},
        "semantic_validator_type": "summary_validator",
    }
    draft = author_behavior_draft_fixture("matrix", goal)
    tests = author_behavior_tests(draft, goal)
    assert tests[0].fixture_events == []
    assert tests[0].expected_events == ["object.created"]
