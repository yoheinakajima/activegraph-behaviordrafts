import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviordrafts.drafts import author_behavior_tests
from behaviordrafts.events import Event
from behaviordrafts.harness import _semantic_diff_matches
from behaviordrafts.llm_author import DEFAULT_MODEL, author_behavior_draft_with_llm
from behaviordrafts.promotion import disable_behavior, promote_behavior
from behaviordrafts.reporting import write_json, write_jsonl
from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.sandbox import compile_runtime_behavior, run_behavior_sandbox
from behaviordrafts.static_analysis import run_static_analysis


def _build_summary(cases, model):
    s = {
        "total_goals": len(cases), "model": model, "llm_attempts": len(cases),
        "parsed_ok": sum(1 for c in cases if c["parsed_ok"]),
        "drafts_created": sum(1 for c in cases if c["draft_created"]),
        "static_analysis_passed": sum(1 for c in cases if c["static_analysis_passed"]),
        "sandbox_passed": sum(1 for c in cases if c["sandbox_passed"]),
        "diff_matches": sum(1 for c in cases if c["diff_match"]),
        "promotions_attempted": sum(1 for c in cases if c["promotion_attempted"]),
        "promotions_succeeded": sum(1 for c in cases if c["promotion_succeeded"]),
        "matching_event_fires": sum(1 for c in cases if c["matching_event_fired"]),
        "nonmatching_event_silent": sum(1 for c in cases if c["nonmatching_event_silent"]),
        "disable_succeeded": sum(1 for c in cases if c["disable_succeeded"]),
        "behavior_silent_after_disable": sum(1 for c in cases if c["behavior_silent_after_disable"]),
        "parse_failures": sum(1 for c in cases if not c["parsed_ok"]),
        "static_failures": sum(1 for c in cases if c["parsed_ok"] and not c["static_analysis_passed"]),
        "sandbox_failures": sum(1 for c in cases if c["static_analysis_passed"] and not c["sandbox_passed"]),
        "semantic_failures": sum(1 for c in cases if c["sandbox_passed"] and not c["diff_match"]),
    }
    return s


def _build_markdown(cases, summary):
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    failures = {}
    for c in cases:
        for e in c["errors"]:
            failures[e] = failures.get(e, 0) + 1
    frows = [f"| {k} | {v} |" for k, v in sorted(failures.items())] or ["| none | 0 |"]
    per_goal = [
        f"| {c['goal_id']} | {c['parsed_ok']} | {c['static_analysis_passed']} | {c['sandbox_passed']} | {c['diff_match']} | {c['promotion_succeeded']} | {c['outcome']} |"
        for c in cases
    ]
    all_pass = all(c["outcome"] == "passed" for c in cases)
    interp = "LLM-authored drafts passed the bounded lifecycle checks for these two goals." if all_pass else "Some LLM-authored drafts failed bounded lifecycle checks; see failure breakdown for exact stages."
    interp += " This two-goal run is a narrow measurement and should not be treated as broad reliability evidence."
    return "\n".join([
        "# Live LLM Authorship Run", "", f"- Timestamp (UTC): {ts}", f"- Model: {summary['model']}", "",
        "## Aggregate Metrics", "", "| Metric | Value |", "|---|---:|",
        *[f"| {k} | {v} |" for k, v in summary.items()], "",
        "## Per-goal Results", "", "| Goal | Parsed | Static pass | Sandbox pass | Semantic diff pass | Promoted | Outcome |", "|---|---|---|---|---|---|---|", *per_goal,
        "", "## Failure Breakdown", "", "| Failure | Count |", "|---|---:|", *frows, "", "## Interpretation", "", interp, ""
    ])


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required for scripts/run_live_llm.py. Skipping live run.")
        return 2

    goals = json.loads(Path("experiments/goals.json").read_text(encoding="utf-8"))
    model = os.getenv("BEHAVIORDRAFTS_MODEL", DEFAULT_MODEL)
    cases, prompts, raws = [], [], []

    for goal in goals:
        runtime = EventSourcedRuntime()
        case = {
            "goal_id": goal["goal_name"], "goal": goal["description"], "model": model,
            "prompt_hash": None, "raw_response_recorded": False, "parsed_ok": False, "parse_error": None,
            "draft_created": False, "static_analysis_passed": False, "static_analysis_errors": [],
            "sandbox_created": False, "sandbox_passed": False, "source_compiled": False,
            "sandbox_executed_generated_source": False, "source_execution_error": None, "diff_match": False,
            "promotion_attempted": False, "promotion_succeeded": False, "matching_event_fired": False,
            "nonmatching_event_silent": False, "disable_succeeded": False, "behavior_silent_after_disable": False,
            "outcome": "failed", "errors": []
        }
        draft, meta = author_behavior_draft_with_llm(goal, {"condition": "C", "goal": goal["goal_name"]}, model=model)
        case["prompt_hash"] = meta.get("prompt_hash")
        case["raw_response_recorded"] = bool(meta.get("raw_response"))
        case["parsed_ok"] = bool(meta.get("parsed_ok"))
        case["parse_error"] = meta.get("parse_error")
        prompts.append({"goal_id": goal["goal_name"], "model": model, "prompt_hash": meta.get("prompt_hash"), "prompt": meta.get("prompt", "")})
        raws.append({"goal_id": goal["goal_name"], "model": model, "prompt_hash": meta.get("prompt_hash"), "raw_response": meta.get("raw_response", ""), "parse_error": meta.get("parse_error")})
        if draft is None:
            case["errors"].append("parse_failed")
            cases.append(case)
            continue

        case["draft_created"] = True
        analysis = run_static_analysis(draft)
        case["static_analysis_passed"] = analysis.analysis_passed
        case["static_analysis_errors"] = analysis.errors
        if not analysis.analysis_passed:
            case["errors"].append("static_analysis_failed")

        tests = author_behavior_tests(draft, goal)
        trigger = Event("object.created", {"object": goal["trigger_object"]})
        sandbox = run_behavior_sandbox(runtime, draft, None, trigger, tests, goal["budgets"], analysis_passed=analysis.analysis_passed)
        case["sandbox_created"] = True
        case["sandbox_passed"] = sandbox.sandbox_passed
        case["source_compiled"] = sandbox.source_compiled
        case["sandbox_executed_generated_source"] = sandbox.sandbox_executed_generated_source
        case["source_execution_error"] = sandbox.source_execution_error
        if not sandbox.sandbox_passed:
            case["errors"].append("sandbox_failed")

        case["diff_match"] = sandbox.sandbox_passed and _semantic_diff_matches(goal["goal_name"], goal["trigger_object"], sandbox.structural_diff)
        if not case["diff_match"]:
            case["errors"].append("semantic_diff_failed")

        case["promotion_attempted"] = True
        decision = promote_behavior(runtime, draft, analysis, sandbox, compile_runtime_behavior(draft.source_code))
        case["promotion_succeeded"] = decision.decision == "approved"
        if case["promotion_succeeded"]:
            binding_id = next(iter(runtime.behaviors))
            runtime.emit(trigger)
            case["matching_event_fired"] = any(o.get("type") in ["Summary", "Evaluation"] for o in runtime.graph.objects.values())
            before = len(runtime.events)
            runtime.emit(Event("object.created", {"object": {"id": "unrelated-1", "type": "Unrelated"}}))
            after = len(runtime.events)
            case["nonmatching_event_silent"] = after == before + 1
            disable_behavior(runtime, binding_id)
            case["disable_succeeded"] = not runtime.behaviors[binding_id].enabled
            before_disable = len(runtime.events)
            runtime.emit(trigger)
            case["behavior_silent_after_disable"] = len(runtime.events) == before_disable + 1

        case["outcome"] = "passed" if case["promotion_succeeded"] and case["disable_succeeded"] and case["behavior_silent_after_disable"] else "failed"
        cases.append(case)

    summary = _build_summary(cases, model)
    write_jsonl("results/live_llm_cases.jsonl", cases)
    write_jsonl("results/live_llm_prompts.jsonl", prompts)
    write_jsonl("results/live_llm_raw_responses.jsonl", raws)
    write_json("results/live_llm_summary.json", summary)
    Path("results/live_llm_summary.md").write_text(_build_markdown(cases, summary), encoding="utf-8")
    print("wrote live LLM results to results/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
