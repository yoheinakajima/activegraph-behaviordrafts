import json
from pathlib import Path

from behaviordrafts.live_llm_matrix import SEMANTIC_VALIDATORS, aggregate_summary, assign_failure_stage, semantic_diff_matches


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
    c1 = {"goal_id": "g1", "parsed_ok": True, "static_analysis_passed": True, "sandbox_passed": True, "diff_match": True, "promotion_attempted": True, "promotion_succeeded": True, "matching_event_fired": True, "nonmatching_event_silent": True, "disable_succeeded": True}
    c1["failure_stage"] = assign_failure_stage(c1)
    c2 = dict(c1)
    c2.update({"goal_id": "g2", "parsed_ok": False})
    c2["failure_stage"] = assign_failure_stage(c2)
    summary = aggregate_summary([c1, c2], "gpt-test", 2, 1)
    assert summary["full_successes"] == 1
    assert summary["parse_failures"] == 1
    assert c2["failure_stage"] == "parse"
