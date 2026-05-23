import sys
import types

from behaviordrafts.activegraph_adapter import ActiveGraphAdapter
from behaviordrafts.adversarial import run_adversarial_experiments
from behaviordrafts.harness import run_experiments


def _install_fake_activegraph(monkeypatch):
    class FakeGraph:
        def __init__(self):
            self.objects_store = {}
            self.relations_store = []
            self.emitted = []

        def add_object(self, type, data, actor="system", caused_by=None):
            obj = {"id": data.get("id", f"obj-{len(self.objects_store)+1}"), "type": type, **data}
            self.objects_store[obj["id"]] = obj
            return obj

        def add_relation(self, source, target, type, data=None, actor="system", caused_by=None):
            rel = {"id": f"rel-{len(self.relations_store)+1}", "from": source, "to": target, "type": type, **(data or {})}
            self.relations_store.append(rel)
            return rel

        def emit(self, event):
            self.emitted.append(event)

        def all_objects(self):
            return list(self.objects_store.values())

        def all_relations(self):
            return list(self.relations_store)

        def objects(self, type=None, where=None):
            return [o for o in self.objects_store.values() if type is None or o.get("type") == type]

        def relations(self, source=None, target=None, type=None):
            return [r for r in self.relations_store if (source is None or r.get("from") == source) and (target is None or r.get("to") == target) and (type is None or r.get("type") == type)]

        def get_object(self, id_):
            return self.objects_store[id_]

        def get_relation(self, id_):
            return next(r for r in self.relations_store if r["id"] == id_)

    class FakeRuntime:
        def __init__(self, graph, behaviors=None):
            self.graph = graph
            self.behaviors = behaviors or []

        def fork(self, at_event, label=None, behaviors=None):
            return FakeRuntime(self.graph, behaviors=behaviors or self.behaviors)

        def diff(self, other):
            return {"ok": True}

    class FakeEvent:
        def __init__(self, id, type, payload=None, actor=None, frame_id=None, caused_by=None, timestamp=""):
            self.id = id
            self.type = type
            self.payload = payload or {}

    class FakeBehavior:
        def __init__(self, name, fn, on=None, **kwargs):
            self.name = name
            self.fn = fn
            self.on = on or []

    fake = types.SimpleNamespace(
        __version__="1.0.5.post2",
        Graph=FakeGraph,
        Runtime=FakeRuntime,
        Event=FakeEvent,
        Behavior=FakeBehavior,
    )
    monkeypatch.setitem(sys.modules, "activegraph", fake)


def test_adapter_unavailable_is_honestly_labeled_local_shim():
    adapter = ActiveGraphAdapter(allow_local_shim=False)
    if adapter.activegraph_available is False:
        assert adapter.backend_kind == "activegraph_import_probe_local_shim"


def test_adapter_uses_real_primitives_when_available(monkeypatch):
    from behaviordrafts import activegraph_adapter as aa
    _install_fake_activegraph(monkeypatch)
    monkeypatch.setattr(aa, "probe_activegraph", lambda: type("P", (), {"available": True, "module": "activegraph", "reason": "ok"})())
    adapter = ActiveGraphAdapter(allow_local_shim=False)
    assert adapter.activegraph_available is True
    assert adapter.runtime.__class__.__name__ == "FakeRuntime"
    assert adapter.graph.__class__.__name__ == "FakeGraph"

    adapter.add_object("Summary", {"id": "s1", "line_count": 1})
    adapter.add_relation("s1", "f1", "summarizes", {})
    adapter.emit_event("object.created", {"object": {"id": "f1", "type": "File"}})

    assert any(f == "activegraph.Graph" for f in adapter.activegraph_native_features)
    assert any(f == "Graph.add_object" for f in adapter.activegraph_native_features)
    assert any(f == "Graph.emit" for f in adapter.activegraph_native_features)
    assert any(f == "activegraph.Behavior" for f in adapter.activegraph_native_features)
    assert adapter.graph.emitted, "emit_event should emit activegraph.Event"


def test_result_summaries_record_backend_identity(monkeypatch):
    monkeypatch.setenv("BEHAVIORDRAFTS_BACKEND", "local_shim")
    out = run_experiments(use_llm=False)
    first = out[0]
    assert first["backend_kind"] == "activegraph_adapter"
    assert first["activegraph_available"] is not None
    assert first["activegraph_native_features"] is not None
    assert first["adapter_shim_features"] is not None
    assert first["backend_details"] is not None
    assert first["activegraph_native_features"] != ["import_probe"]


def test_adversarial_uses_adapter_backend(monkeypatch):
    monkeypatch.setenv("BEHAVIORDRAFTS_BACKEND", "local_shim")
    out = run_adversarial_experiments()
    assert out["summary"]["backend_kind"] == "activegraph_adapter"
    assert out["summary"]["activegraph_available"] is not None
    assert out["summary"]["activegraph_native_features"] is not None
    assert out["summary"]["adapter_shim_features"] is not None
    assert out["summary"]["backend_details"] is not None
    assert all(row["backend_kind"] == "activegraph_adapter" for row in out["cases"])
