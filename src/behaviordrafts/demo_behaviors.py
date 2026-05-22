from .events import Event


def file_summary_behavior(event, graph):
    obj = event.payload["object"]
    content = obj.get("content", "")
    first = (content.split(".")[0].strip() + ".") if "." in content else content.strip()
    line_count = len(content.splitlines()) if content else 0
    sid = f"summary-{obj['id']}"
    summary = {"id": sid, "type": "Summary", "first_sentence": first, "line_count": line_count}
    return [
        Event("object.created", {"object": summary}),
        Event("relation.created", {"relation": {"type": "summarizes", "from": sid, "to": obj["id"]}}),
    ]


def provenance_auditor_behavior(event, graph):
    obj = event.payload["object"]
    changes = obj.get("changes", [])
    missing = sum(1 for c in changes if not c.get("provenance"))
    eid = f"eval-{obj['id']}"
    evaluation = {"id": eid, "type": "Evaluation", "passes": missing == 0, "missing_provenance_count": missing}
    return [Event("object.created", {"object": evaluation})]
