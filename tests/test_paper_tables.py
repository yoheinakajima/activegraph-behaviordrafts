import json
import subprocess
from pathlib import Path


def _run(cmd):
    subprocess.run(cmd, shell=True, check=True)


def test_paper_table_script_generates_required_outputs_and_titles():
    _run("python scripts/clean_results.py")
    _run("python scripts/run_all.py")
    _run("python scripts/run_adversarial.py")
    _run("python scripts/generate_paper_tables.py")

    md = Path("results/paper_tables.md").read_text(encoding="utf-8")
    assert "Table 1: Deterministic lifecycle baseline" in md
    assert "Table 2: Behavior-draft lifecycle gates" in md
    assert "Table 3: Adversarial containment" in md
    assert "Table 4: Runtime parity / authority boundary" in md

    data = json.loads(Path("results/paper_tables.json").read_text(encoding="utf-8"))
    assert "table_1_deterministic_lifecycle_baseline" in data
    assert "table_2_behavior_draft_lifecycle_gates" in data
    assert "table_3_adversarial_containment" in data
    assert "table_4_runtime_parity_authority_boundary" in data


def test_paper_tables_artifacts_untracked_by_gitignore():
    gi = Path('.gitignore').read_text(encoding='utf-8')
    assert "results/*.json" in gi
    assert "results/*.md" in gi


def test_table_counts_match_summary_sources():
    _run("python scripts/clean_results.py")
    _run("python scripts/run_all.py")
    _run("python scripts/run_adversarial.py")
    _run("python scripts/generate_paper_tables.py")

    tables = json.loads(Path("results/paper_tables.json").read_text(encoding="utf-8"))
    summary_rows = json.loads(Path("results/summary.json").read_text(encoding="utf-8"))
    adv_summary = json.loads(Path("results/adversarial_summary.json").read_text(encoding="utf-8"))

    t1 = tables["table_1_deterministic_lifecycle_baseline"]
    assert sum(r["runs"] for r in t1) == len(summary_rows)

    t3 = tables["table_3_adversarial_containment"]
    assert sum(r["cases"] for r in t3) == adv_summary["total_cases"]
    assert sum(r["unexpected_passes"] for r in t3) == adv_summary["unexpected_passes"]
    assert sum(r["unexpected_failures"] for r in t3) == adv_summary["unexpected_failures"]
