from behaviordrafts.activegraph_adapter import ActiveGraphAdapter
from behaviordrafts.activegraph_backend import probe_activegraph
from behaviordrafts.adversarial import run_adversarial_experiments
from behaviordrafts.harness import run_experiments


def test_activegraph_import_probe_runs():
    probe = probe_activegraph()
    assert probe.module == "activegraph"
    assert isinstance(probe.available, bool)


def test_adapter_constructible_with_explicit_shim_opt_in_when_missing():
    probe = probe_activegraph()
    if not probe.available:
        adapter = ActiveGraphAdapter(allow_local_shim=True)
        assert adapter.backend_kind == "activegraph_adapter"
        assert "create_runtime_graph" in adapter.adapter_shim_features


def test_adapter_no_silent_fallback_without_opt_in():
    probe = probe_activegraph()
    if not probe.available:
        try:
            ActiveGraphAdapter(allow_local_shim=False)
        except RuntimeError as exc:
            assert "allow_local_shim=True" in str(exc)
        else:
            raise AssertionError("adapter must fail closed when activegraph is unavailable")


def test_result_summaries_record_backend_identity(monkeypatch):
    monkeypatch.setenv("BEHAVIORDRAFTS_ALLOW_LOCAL_SHIM", "1")
    out = run_experiments(use_llm=False)
    first = out[0]
    assert first["backend_kind"] == "activegraph_adapter"
    assert "activegraph_available" in first
    assert "adapter_shim_features" in first


def test_adversarial_uses_adapter_backend(monkeypatch):
    monkeypatch.setenv("BEHAVIORDRAFTS_ALLOW_LOCAL_SHIM", "1")
    out = run_adversarial_experiments()
    assert out["summary"]["backend_kind"] == "activegraph_adapter"
    assert all(row["backend_kind"] == "activegraph_adapter" for row in out["cases"])
