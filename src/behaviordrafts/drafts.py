from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import hashlib
import uuid


@dataclass
class BehaviorDraft:
    id: str
    name: str
    description: str
    source_code: str
    declared_trigger_events: List[str]
    declared_scope: Dict[str, Any]
    declared_inputs: List[str]
    declared_outputs: List[str]
    declared_permissions: List[str]
    declared_dependencies: List[str]
    expected_emitted_events: List[str]
    expected_graph_mutations: Dict[str, Any]
    created_by: str
    created_from_goal: str
    model_used: str
    prompt_hash: str
    status: str


@dataclass
class BehaviorTest:
    id: str
    draft_id: str
    test_name: str
    fixture_events: List[Dict[str, Any]]
    fixture_graph: Dict[str, Any]
    expected_events: List[str]
    expected_objects: List[str]
    expected_relations: List[str]
    expected_diff: Dict[str, Any]
    test_source: str
    created_by: str


def author_behavior_draft_fixture(name: str, goal: Dict[str, Any]) -> BehaviorDraft:
    source = goal["source_code"]
    return BehaviorDraft(
        id=str(uuid.uuid4()), name=name, description=goal["description"], source_code=source,
        declared_trigger_events=["object.created"], declared_scope=goal["scope"], declared_inputs=["event", "graph"],
        declared_outputs=["events"], declared_permissions=["emit.object.created"], declared_dependencies=goal.get("declared_dependencies", []),
        expected_emitted_events=["object.created"], expected_graph_mutations=goal["expected_diff"], created_by="fixture",
        created_from_goal=goal["goal_name"], model_used="none", prompt_hash=hashlib.sha256(source.encode()).hexdigest(), status="drafted"
    )


def author_behavior_tests(draft: BehaviorDraft, goal: Dict[str, Any]) -> List[BehaviorTest]:
    t = BehaviorTest(
        id=str(uuid.uuid4()), draft_id=draft.id, test_name=f"{draft.name}_basic", fixture_events=goal["fixture_events"],
        fixture_graph=goal.get("fixture_graph", {}), expected_events=goal["expected_events"],
        expected_objects=goal.get("expected_objects", []), expected_relations=goal.get("expected_relations", []),
        expected_diff=goal["expected_diff"], test_source="template", created_by="fixture"
    )
    return [t]


def to_dict(x):
    return asdict(x)
