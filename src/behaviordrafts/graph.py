from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GraphState:
    objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)

    def clone(self) -> "GraphState":
        return GraphState(objects={k: dict(v) for k, v in self.objects.items()}, relations=[dict(r) for r in self.relations])

    def structural_diff(self, other: "GraphState") -> Dict[str, Any]:
        created_objects = [oid for oid in self.objects if oid not in other.objects]
        created_relations = [r for r in self.relations if r not in other.relations]
        return {
            "objects_created": len(created_objects),
            "relations_created": len(created_relations),
            "created_object_ids": created_objects,
            "created_objects": [dict(self.objects[oid]) for oid in created_objects],
            "created_relations": created_relations,
        }
