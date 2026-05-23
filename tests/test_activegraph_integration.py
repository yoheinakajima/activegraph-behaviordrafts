from behaviordrafts.activegraph_backend import probe_activegraph, require_activegraph
from behaviordrafts.runtime import EventSourcedRuntime


def test_runtime_declares_backend_kind():
    runtime = EventSourcedRuntime()
    assert runtime.backend_kind in {"local_shim", "activegraph", "activegraph_adapter"}


def test_activegraph_probe_explicit_when_unavailable():
    probe = probe_activegraph()
    if not probe.available:
        assert "unavailable" in ("activegraph is unavailable")


def test_require_activegraph_fails_closed_when_missing():
    probe = probe_activegraph()
    if not probe.available:
        try:
            require_activegraph()
        except RuntimeError as exc:
            assert "required" in str(exc)
        else:
            raise AssertionError("require_activegraph() must fail closed when activegraph is missing")
