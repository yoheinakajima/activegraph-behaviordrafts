from pathlib import Path

from behaviordrafts.adversarial import adversarial_cases, run_adversarial_experiments


def _rows_by(cat, rows):
    return [r for r in rows if r["category"] == cat]


def test_adversarial_case_ids_unique():
    ids = [c.case_id for c in adversarial_cases()]
    assert len(ids) == len(set(ids))


def test_adversarial_expected_gate_behavior_and_summary_counts():
    out = run_adversarial_experiments()
    rows = out["cases"]
    summary = out["summary"]

    assert all(not r["static_analysis_passed"] for r in _rows_by("static_reject", rows))
    assert all(not r["promotion_succeeded"] for r in _rows_by("sandbox_reject", rows))
    assert all(not r["promotion_succeeded"] for r in _rows_by("semantic_reject", rows))
    assert all(r["promotion_succeeded"] for r in _rows_by("benign_control", rows))

    rejected = [r for r in rows if r["category"] != "benign_control"]
    assert all(r["live_graph_unchanged"] for r in rejected)

    assert summary["total_cases"] == len(rows)
    assert summary["static_reject_cases"] == 16
    assert summary["sandbox_reject_cases"] == 5
    assert summary["semantic_reject_cases"] == 6
    assert summary["benign_control_cases"] == 2
    assert summary["direct_mutation_cases"] >= 6
    assert summary["direct_mutation_rejected"] == summary["direct_mutation_cases"]

    direct_mutation = [r for r in rows if "mutat" in r["case_id"] or r["case_id"].startswith("ctx_")]
    assert all(not r["promotion_succeeded"] for r in direct_mutation)
    assert all(r["live_graph_unchanged"] for r in direct_mutation)


def test_adversarial_result_files_ignored_by_git():
    gi = Path('.gitignore').read_text(encoding='utf-8')
    for patt in ["results/*.json", "results/*.jsonl", "results/*.md"]:
        assert patt in gi


def test_adversarial_summary_markdown_has_tables():
    run_adversarial_experiments()
    md = Path("results/adversarial_summary.md").read_text(encoding="utf-8")
    assert "# Adversarial Behavior Report" in md
    assert "| Metric | Value |" in md
    assert "| Category | Cases |" in md
