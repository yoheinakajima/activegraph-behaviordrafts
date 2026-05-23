from pathlib import Path


def test_paper_outline_restored_and_contains_required_sections():
    text = Path("docs/paper_outline.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) > 100
    assert "## 5. Paper outline" in text
    assert "## 9. Claims and non-claims" in text


def test_live_matrix_results_restored_and_contains_snapshot_metrics():
    text = Path("docs/live_llm_matrix_results.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) > 60
    assert "Total trials: 69" in text
    assert "full_successes | 60" in text
    assert "semantic_failures | 3" in text
