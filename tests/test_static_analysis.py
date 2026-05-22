from behaviordrafts.drafts import author_behavior_draft_fixture
from behaviordrafts.static_analysis import run_static_analysis


def test_static_analysis_blocks_eval():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n eval('1')","scope":{},"expected_diff":{},"goal_name":"g"}
    d = author_behavior_draft_fixture("bad", goal)
    r = run_static_analysis(d)
    assert not r.analysis_passed


def test_static_analysis_blocks_open_exec_import_abuse():
    goal = {"description":"x","source_code":"import subprocess\ndef behavior(event, graph, ctx):\n open('/tmp/x')\n exec('1')","scope":{},"expected_diff":{},"goal_name":"g","declared_dependencies":["subprocess"]}
    d = author_behavior_draft_fixture("bad", goal)
    r = run_static_analysis(d)
    assert not r.analysis_passed


def test_static_analysis_blocks_direct_graph_and_ctx_internal_mutation():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n graph.objects.clear()\n graph.relations.append({'x':1})\n setattr(graph, 'objects', {})\n ctx.__dict__['_events']=[]\n ctx.runtime.append_event(event)","scope":{},"expected_diff":{},"goal_name":"g"}
    d = author_behavior_draft_fixture("bad", goal)
    r = run_static_analysis(d)
    assert not r.analysis_passed
    assert any("graph.objects" in v for v in r.permission_violations)
    assert any("ctx.__dict__" in v for v in r.permission_violations)
