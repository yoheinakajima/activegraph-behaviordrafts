from behaviordrafts.activegraph_adapter import ActiveGraphAdapter
from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests
from behaviordrafts.events import Event
from behaviordrafts.sandbox import run_behavior_sandbox
from behaviordrafts.static_analysis import run_static_analysis


class _NoCloneGraph:
    def __init__(self):
        self._objects = []
        self._relations = []

    def all_objects(self):
        return list(self._objects)

    def all_relations(self):
        return list(self._relations)

    def objects(self, type=None):
        return [o for o in self._objects if type is None or getattr(o, "type", None) == type]

    def relations(self, source=None, target=None, type=None):
        return list(self._relations)


def _goal():
    return {
        "goal_name": "file_summary_behavior",
        "description": "x",
        "source_code": "def behavior(event, graph, ctx):\n obj=event['object']\n content=obj.get('content','')\n first=(content.split('.') [0].strip()+'.') if '.' in content else content.strip()\n ctx.emit_object_created({'id':'summary-'+obj['id'],'type':'Summary','first_sentence':first,'line_count':len(content.splitlines())})\n ctx.emit_relation_created({'id':'rel-'+obj['id'],'type':'summarizes','from':'summary-'+obj['id'],'to':obj['id']})",
        "scope": {"object_type": "File"},
        "trigger_object": {"id": "f1", "type": "File", "content": "A.\nB"},
        "expected_objects": ["Summary"],
        "expected_relations": ["summarizes"],
        "expected_diff": {"objects_created": 1, "relations_created": 1},
        "budgets": {"max_emitted_events": 5, "max_objects_created": 3, "max_relations_created": 3, "max_runtime_seconds": 2},
    }


def test_adapter_structural_diff_normalizes_created_entities():
    rt = ActiveGraphAdapter(allow_local_shim=True)
    before = {"objects": [], "relations": [], "event_count": 0}
    after = {
        "objects": [{"id": "s1", "type": "Summary", "first_sentence": "A.", "line_count": 2}],
        "relations": [{"id": "r1", "type": "summarizes", "from": "s1", "to": "f1"}],
        "event_count": 2,
    }
    diff = rt.structural_diff(before, after)
    assert diff["objects_created"] == 1
    assert diff["relations_created"] == 1
    assert diff["events_created"] == 2
    assert diff["created_objects"][0]["type"] == "Summary"
    assert diff["created_relations"][0]["from"] == "s1"


def test_sandbox_avoids_graph_clone_for_adapter_path():
    goal = _goal()
    draft = author_behavior_draft_fixture(goal["goal_name"], goal)
    analysis = run_static_analysis(draft)
    tests = author_behavior_tests(draft, goal)

    rt = ActiveGraphAdapter(allow_local_shim=True)
    rt._ag_graph = _NoCloneGraph()  # no clone method on purpose
    # ensure adapter path is used for snapshot/diff even with non-clone graph
    out = run_behavior_sandbox(rt, draft, None, Event("object.created", {"object": goal["trigger_object"]}), tests, goal["budgets"], analysis_passed=analysis.analysis_passed)

    assert out.sandbox_passed
    assert out.structural_diff["objects_created"] == 1
    assert out.structural_diff["relations_created"] == 1


def test_snapshot_diff_adapter_feature_is_declared():
    rt = ActiveGraphAdapter(allow_local_shim=True)
    assert "snapshot_diff_adapter" in rt.adapter_shim_features
