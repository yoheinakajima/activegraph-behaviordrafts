import json
from pathlib import Path

from behaviordrafts.harness import _semantic_diff_matches, run_experiments


def _load_summary():
    return json.loads(Path("results/summary.json").read_text(encoding="utf-8"))


def test_summary_md_is_markdown_not_json():
    run_experiments()
    text = Path("results/summary.md").read_text(encoding="utf-8")
    assert text.startswith("# Behavior Draft Experiment Summary")
    assert "| Metric | Value |" in text
    assert not text.lstrip().startswith("{")


def test_total_goals_are_unique_not_runs():
    run_experiments()
    text = Path("results/summary.md").read_text(encoding="utf-8")
    assert "- **Goals:** 2" in text
    assert "- **Total runs:** 6" in text


def test_condition_b_never_promotes():
    run_experiments()
    summary = _load_summary()
    b_runs = [r for r in summary if r["condition"] == "B"]
    assert all(r["draft_created"] for r in b_runs)
    assert all(not r["promotion_attempted"] for r in b_runs)
    assert all(not r["promotion_succeeded"] for r in b_runs)


def test_condition_c_nonmatching_and_disable_semantics():
    run_experiments()
    summary = _load_summary()
    c_runs = [r for r in summary if r["condition"] == "C"]
    assert all(r["promoted_behavior_silent_on_nonmatching_event"] for r in c_runs)
    assert all(r["behavior_silent_after_disable"] for r in c_runs)


def test_file_summary_semantic_match_rejects_bad_line_count():
    trigger = {"id": "file-1", "type": "File", "content": "First sentence.\nSecond line."}
    bad_diff = {
        "created_objects": [{"id": "summary-file-1", "type": "Summary", "first_sentence": "First sentence.", "line_count": 99}],
        "created_relations": [{"type": "summarizes", "from": "summary-file-1", "to": "file-1"}],
    }
    assert not _semantic_diff_matches("file_summary_behavior", trigger, bad_diff)


def test_provenance_semantic_match_rejects_bad_missing_count():
    trigger = {"id": "patch-1", "type": "PatchProposal", "changes": [{"path": "a.py"}, {"path": "b.py", "provenance": "trace-1"}]}
    bad_diff = {
        "created_objects": [{
            "id": "eval-patch-1",
            "type": "Evaluation",
            "patch_proposal_id": "patch-1",
            "missing_provenance_count": 0,
            "passes": True,
        }],
        "created_relations": [],
    }
    assert not _semantic_diff_matches("provenance_auditor_behavior", trigger, bad_diff)


def test_provenance_semantic_match_rejects_missing_patch_proposal_id():
    trigger = {"id": "patch-1", "type": "PatchProposal", "changes": [{"path": "a.py"}]}
    bad_diff = {
        "created_objects": [{
            "id": "eval-patch-1",
            "type": "Evaluation",
            "missing_provenance_count": 1,
            "passes": False,
        }],
        "created_relations": [],
    }
    assert not _semantic_diff_matches("provenance_auditor_behavior", trigger, bad_diff)
