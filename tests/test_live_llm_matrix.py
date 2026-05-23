import json
from pathlib import Path

from behaviordrafts.live_llm_matrix import SEMANTIC_VALIDATORS, aggregate_summary, assign_failure_stage, semantic_diff_matches, validate_matrix_goal


def test_live_goal_corpus_unique_and_required_fields():
    goals = json.loads(Path("experiments/live_llm_goals.json").read_text(encoding="utf-8"))
    ids = [g["goal_id"] for g in goals]
    assert len(ids) == len(set(ids))
    req = {"goal_id", "description", "trigger_object", "scope", "budgets", "expected_objects", "expected_relations", "expected_diff", "semantic_validator_type", "allowed_object_types", "allowed_relation_types"}
    for g in goals:
        assert req.issubset(g.keys())
        assert g["semantic_validator_type"] in SEMANTIC_VALIDATORS


def test_semantic_validators_accept_and_reject():
    goal = {"trigger_object": {"id": "f1", "content": "A.\nB"}, "expected_diff": {"objects_created": 1, "relations_created": 1}, "semantic_validator_type": "summary_validator"}
    good = {"objects_created": 1, "relations_created": 1, "created_objects": [{"type": "Summary", "first_sentence": "A.", "line_count": 2}], "created_relations": [{"type": "summarizes", "to": "f1"}]}
    bad = {"objects_created": 1, "relations_created": 1, "created_objects": [{"type": "Summary", "first_sentence": "X.", "line_count": 2}], "created_relations": [{"type": "summarizes", "to": "f1"}]}
    assert semantic_diff_matches(goal, good)
    assert not semantic_diff_matches(goal, bad)


def test_matrix_summary_and_failure_stage():
    c1 = {"goal_id": "g1", "parsed_ok": True, "draft_created": True, "static_analysis_passed": True, "sandbox_passed": True, "diff_match": True, "promotion_attempted": True, "promotion_succeeded": True, "matching_event_fired": True, "nonmatching_event_silent": True, "disable_succeeded": True}
    c1["failure_stage"] = assign_failure_stage(c1)
    c2 = dict(c1)
    c2.update({"goal_id": "g2", "parsed_ok": False})
    c2["failure_stage"] = assign_failure_stage(c2)
    summary = aggregate_summary([c1, c2], "gpt-test", 2, 1)
    assert summary["full_successes"] == 1
    assert summary["parse_failures"] == 1
    assert c2["failure_stage"] == "parse"


def test_failure_stage_draft_construction_after_successful_parse():
    case = {
        "goal_id": "g3",
        "parsed_ok": True,
        "draft_created": False,
        "static_analysis_passed": False,
        "sandbox_passed": False,
        "diff_match": False,
        "promotion_attempted": False,
        "promotion_succeeded": False,
        "matching_event_fired": False,
        "nonmatching_event_silent": False,
        "disable_succeeded": False,
    }
    assert assign_failure_stage(case) == "draft_construction"


def test_failure_stage_test_construction_after_draft_creation():
    case = {
        "goal_id": "g4",
        "parsed_ok": True,
        "draft_created": True,
        "errors": ["test_construction_error: missing expected_diff"],
        "static_analysis_passed": True,
        "sandbox_passed": False,
        "diff_match": False,
        "promotion_attempted": False,
        "promotion_succeeded": False,
        "matching_event_fired": False,
        "nonmatching_event_silent": False,
        "disable_succeeded": False,
    }
    assert assign_failure_stage(case) == "test_construction"


def test_validate_matrix_goal_catches_missing_required_fields():
    goal = {
        "goal_id": "bad",
        "description": "bad goal",
        "scope": {"object_type": "File"},
    }
    try:
        validate_matrix_goal(goal)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "missing required fields" in str(exc)


def test_summary_validator_rejects_missing_required_fields():
    goal = {
        "trigger_object": {"id": "f1", "content": "A.\nB"},
        "expected_diff": {"objects_created": 1, "relations_created": 1},
        "semantic_validator_type": "summary_validator",
    }
    missing_first = {
        "objects_created": 1,
        "relations_created": 1,
        "created_objects": [{"type": "Summary", "line_count": 2}],
        "created_relations": [{"type": "summarizes", "to": "f1"}],
    }
    missing_count = {
        "objects_created": 1,
        "relations_created": 1,
        "created_objects": [{"type": "Summary", "first_sentence": "A."}],
        "created_relations": [{"type": "summarizes", "to": "f1"}],
    }
    assert not semantic_diff_matches(goal, missing_first)
    assert not semantic_diff_matches(goal, missing_count)
