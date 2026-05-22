from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.promotion import promote_behavior
from behaviordrafts.static_analysis import run_static_analysis
from behaviordrafts.sandbox import run_behavior_sandbox
from behaviordrafts.events import Event
from behaviordrafts.drafts import author_behavior_draft_fixture, author_behavior_tests


def test_promotion_requires_gates():
    goal = {"description":"x","source_code":"def behavior(event, graph, ctx):\n obj=event['object']\n ctx.emit_object_created({'id':'eval-'+obj['id'],'type':'Evaluation','patch_proposal_id':obj['id'],'passes':False,'missing_provenance_count':1})","scope":{"object_type":"PatchProposal"},"expected_diff":{"objects_created":1},"goal_name":"provenance_auditor_behavior","fixture_events":[],"expected_events":[],"expected_objects":["Evaluation"],"expected_relations":[]}
    d = author_behavior_draft_fixture("x", goal)
    t = author_behavior_tests(d, goal)
    a = run_static_analysis(d)
    s = run_behavior_sandbox(EventSourcedRuntime(), d, None, Event("object.created", {"object":{"id":"1","type":"PatchProposal","changes":[{}]}}), t, {"max_emitted_events":3,"max_objects_created":2,"max_relations_created":1,"max_runtime_seconds":2})
    dec = promote_behavior(EventSourcedRuntime(), d, a, s, lambda event, graph, metadata: [])
    assert dec.decision == "approved"
