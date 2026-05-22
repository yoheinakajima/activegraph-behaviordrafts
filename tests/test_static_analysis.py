from behaviordrafts.drafts import author_behavior_draft_fixture
from behaviordrafts.static_analysis import run_static_analysis


def test_static_analysis_blocks_eval():
    goal = {"description":"x","source_code":"def behavior(event, graph):\n eval('1')","scope":{},"expected_diff":{},"goal_name":"g"}
    d = author_behavior_draft_fixture("bad", goal)
    r = run_static_analysis(d)
    assert not r.analysis_passed
