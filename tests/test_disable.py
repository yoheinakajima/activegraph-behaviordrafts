from behaviordrafts.runtime import EventSourcedRuntime, BoundBehavior
from behaviordrafts.promotion import disable_behavior


def test_disable_flips_enabled():
    rt = EventSourcedRuntime()
    rt.behaviors["b1"] = BoundBehavior("b1", "d", "n", "object.created", {}, {}, True, None)
    disable_behavior(rt, "b1")
    assert rt.behaviors["b1"].enabled is False
