import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


FailureStage = str


def _created(diff: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    return diff.get("created_objects", []) or [], diff.get("created_relations", []) or []


def summary_validator(goal, diff):
    objs, rels = _created(diff)
    if len(objs) != 1:
        return False
    o = objs[0]
    trg = goal["trigger_object"]
    content = trg.get("content", "")
    first = (content.split(".")[0].strip() + ".") if "." in content else content.strip()
    lc = len(content.splitlines()) if content else 0
    if o.get("type") != "Summary" or o.get("first_sentence") != first or o.get("line_count") != lc:
        return False
    return any(r.get("type") == "summarizes" and r.get("to") == trg.get("id") for r in rels)


def todo_extractor_validator(goal, diff):
    objs, _ = _created(diff)
    expected = goal["trigger_object"].get("content", "").count("TODO")
    todos = [o for o in objs if o.get("type") == "TodoFinding"]
    return len(todos) == expected


def heading_count_validator(goal, diff):
    objs, _ = _created(diff)
    counts = [o for o in objs if o.get("type") == "HeadingCount"]
    if len(counts) != 1:
        return False
    content = goal["trigger_object"].get("content", "")
    expected = sum(1 for l in content.splitlines() if l.strip().startswith("#"))
    return counts[0].get("count") == expected


def url_extractor_validator(goal, diff):
    objs, _ = _created(diff)
    u = [o for o in objs if o.get("type") == "URLFinding"]
    return len(u) == 1 and isinstance(u[0].get("url"), str) and u[0].get("url").startswith("http")


def relation_created_validator(goal, diff):
    _, rels = _created(diff)
    er = goal.get("expected_relations", [])
    if not er:
        return False
    return any(r.get("type") == er[0] for r in rels)


def missing_provenance_validator(goal, diff):
    objs, _ = _created(diff)
    e = [o for o in objs if o.get("type") == "Evaluation"]
    if len(e) != 1:
        return False
    changes = goal["trigger_object"].get("changes", [])
    missing = sum(1 for c in changes if not c.get("provenance"))
    return e[0].get("missing_provenance_count") == missing


def classification_validator(goal, diff):
    objs, _ = _created(diff)
    c = [o for o in objs if o.get("type") in ["FileTypeClassification", "PriorityClassification", "RiskClassification"]]
    if len(c) != 1:
        return False
    return c[0].get("label") == goal.get("expected_label")


def schema_violation_validator(goal, diff):
    objs, _ = _created(diff)
    ev = [o for o in objs if o.get("type") == "Evaluation"]
    return len(ev) == 1 and bool(ev[0].get("violates_schema"))


SEMANTIC_VALIDATORS: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], bool]] = {
    "summary_validator": summary_validator,
    "todo_extractor_validator": todo_extractor_validator,
    "heading_count_validator": heading_count_validator,
    "url_extractor_validator": url_extractor_validator,
    "relation_created_validator": relation_created_validator,
    "missing_provenance_validator": missing_provenance_validator,
    "classification_validator": classification_validator,
    "schema_violation_validator": schema_violation_validator,
}


def semantic_diff_matches(goal: Dict[str, Any], diff: Dict[str, Any]) -> bool:
    expected = goal.get("expected_diff", {})
    if diff.get("objects_created", 0) != expected.get("objects_created", 0):
        return False
    if diff.get("relations_created", 0) != expected.get("relations_created", 0):
        return False
    fn = SEMANTIC_VALIDATORS.get(goal.get("semantic_validator_type"))
    return bool(fn and fn(goal, diff))


def assign_failure_stage(case: Dict[str, Any]) -> FailureStage:
    if not case.get("parsed_ok"):
        return "parse"
    if not case.get("static_analysis_passed"):
        return "static_analysis"
    if not case.get("sandbox_passed"):
        return "sandbox"
    if not case.get("diff_match"):
        return "semantic_diff"
    if case.get("promotion_attempted") and not case.get("promotion_succeeded"):
        return "promotion"
    if not case.get("matching_event_fired"):
        return "matching_event"
    if not case.get("nonmatching_event_silent"):
        return "nonmatching_event"
    if not case.get("disable_succeeded"):
        return "disable"
    return "none"


def aggregate_summary(cases: List[Dict[str, Any]], model: str, goals: int, trials_per_goal: int) -> Dict[str, Any]:
    out = {
        "model": model, "goals": goals, "trials_per_goal": trials_per_goal, "total_trials": len(cases),
        "parsed_ok": sum(c["parsed_ok"] for c in cases), "static_analysis_passed": sum(c["static_analysis_passed"] for c in cases),
        "sandbox_passed": sum(c["sandbox_passed"] for c in cases), "diff_matches": sum(c["diff_match"] for c in cases),
        "promotions_succeeded": sum(c["promotion_succeeded"] for c in cases), "matching_event_fires": sum(c["matching_event_fired"] for c in cases),
        "nonmatching_event_silent": sum(c["nonmatching_event_silent"] for c in cases), "disable_succeeded": sum(c["disable_succeeded"] for c in cases),
    }
    out["full_successes"] = sum(1 for c in cases if assign_failure_stage(c) == "none")
    out["parse_failures"] = sum(1 for c in cases if c["failure_stage"] == "parse")
    out["static_failures"] = sum(1 for c in cases if c["failure_stage"] == "static_analysis")
    out["sandbox_failures"] = sum(1 for c in cases if c["failure_stage"] == "sandbox")
    out["semantic_failures"] = sum(1 for c in cases if c["failure_stage"] == "semantic_diff")
    out["promotion_failures"] = sum(1 for c in cases if c["failure_stage"] == "promotion")
    out["matching_event_failures"] = sum(1 for c in cases if c["failure_stage"] == "matching_event")
    out["nonmatching_event_failures"] = sum(1 for c in cases if c["failure_stage"] == "nonmatching_event")
    out["disable_failures"] = sum(1 for c in cases if c["failure_stage"] == "disable")
    per_goal = defaultdict(lambda: {"trials": 0, "full_successes": 0})
    for c in cases:
        pg = per_goal[c["goal_id"]]
        pg["trials"] += 1
        pg["full_successes"] += 1 if c["failure_stage"] == "none" else 0
    out["per_goal"] = dict(per_goal)
    out["per_failure_stage"] = dict(Counter(c["failure_stage"] for c in cases))
    return out


def build_markdown(summary: Dict[str, Any]) -> str:
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = ["# Live LLM Reliability Matrix", "", f"- Timestamp: {ts}", f"- Model: {summary['model']}", f"- Number of goals: {summary['goals']}", f"- Trials per goal: {summary['trials_per_goal']}", "", "## Aggregate Metrics", "", "| Metric | Value |", "|---|---:|"]
    for k, v in summary.items():
        if k in ["per_goal", "per_failure_stage"]:
            continue
        lines.append(f"| {k} | {v} |")
    lines += ["", "## Per-goal", "", "| Goal | Trials | Full Successes |", "|---|---:|---:|"]
    for g, vals in sorted(summary["per_goal"].items()):
        lines.append(f"| {g} | {vals['trials']} | {vals['full_successes']} |")
    lines += ["", "## Failure-stage breakdown", "", "| Stage | Count |", "|---|---:|"]
    for st, ct in sorted(summary["per_failure_stage"].items()):
        lines.append(f"| {st} | {ct} |")
    lines += ["", "## Interpretation", "", "This bounded corpus estimates lifecycle reliability for inert BehaviorDraft authoring under existing gates.", "This is not a broad reliability claim across open-ended tasks."]
    return "\n".join(lines) + "\n"
