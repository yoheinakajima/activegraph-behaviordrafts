from .events import Event


def file_summary_behavior(event, graph):
    obj = event.payload["object"]
    content = obj.get("content", "")
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    joined = " ".join(lines)
    first = (joined.split(".")[0].strip() + ".") if "." in joined else (lines[0] if lines else "")
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
    evaluation = {
        "id": eid,
        "type": "Evaluation",
        "patch_proposal_id": obj.get("id"),
        "passes": missing == 0,
        "missing_provenance_count": missing,
    }
    return [Event("object.created", {"object": evaluation})]
