from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.events import Event


def test_replay_projection_equivalence():
    rt = EventSourcedRuntime()
    ev = Event("object.created", {"object": {"id": "1", "type": "File"}})
    rt.emit(ev)
    rt2 = EventSourcedRuntime()
    for e in rt.events:
        rt2.apply_event(e)
    assert rt2.graph.objects["1"]["type"] == "File"
