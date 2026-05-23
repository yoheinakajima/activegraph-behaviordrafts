import json
import subprocess
import sys
from pathlib import Path


def test_run_live_llm_missing_key_exits_gracefully(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cp = subprocess.run([sys.executable, "scripts/run_live_llm.py"], capture_output=True, text=True)
    assert cp.returncode == 2
    assert "OPENAI_API_KEY is required" in cp.stdout


def test_generate_paper_tables_without_live_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("results").mkdir()
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "generate_paper_tables.py")], check=True)
    out = Path("results/paper_tables.md").read_text(encoding="utf-8")
    assert "Live LLM results not present" in out


def test_generate_paper_tables_with_live_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("results").mkdir()
    Path("results/live_llm_summary.json").write_text(json.dumps({
        "total_goals": 2, "model": "gpt-4o-mini", "parsed_ok": 2,
        "static_analysis_passed": 2, "sandbox_passed": 2, "diff_matches": 2,
        "promotions_succeeded": 2, "matching_event_fires": 2, "disable_succeeded": 2,
        "parse_failures": 0, "static_failures": 0, "sandbox_failures": 0, "semantic_failures": 0
    }), encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "generate_paper_tables.py")], check=True)
    out = Path("results/paper_tables.md").read_text(encoding="utf-8")
    assert "Table 5: Live LLM Authorship Run" in out
    assert "gpt-4o-mini" in out


def test_live_generated_artifacts_ignored_by_git():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "results/*.json" in gitignore
    assert "results/*.jsonl" in gitignore
    assert "results/*.md" in gitignore


def test_live_summary_writer_with_mocked_case_data():
    import sys
    sys.path.insert(0, "scripts")
    import run_live_llm
    cases = [{"parsed_ok": True, "draft_created": True, "static_analysis_passed": True, "sandbox_passed": True, "diff_match": True, "promotion_attempted": True, "promotion_succeeded": True, "matching_event_fired": True, "nonmatching_event_silent": True, "disable_succeeded": True, "behavior_silent_after_disable": True}]
    summary = run_live_llm._build_summary(cases, "gpt-test")
    assert summary["model"] == "gpt-test"
    assert summary["total_goals"] == 1
    assert summary["promotions_succeeded"] == 1
