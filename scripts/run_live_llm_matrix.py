import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviordrafts.drafts import author_behavior_tests
from behaviordrafts.events import Event
from behaviordrafts.live_llm_matrix import aggregate_summary, assign_failure_stage, build_markdown, semantic_diff_matches, validate_matrix_goal
from behaviordrafts.llm_author import DEFAULT_MODEL, author_behavior_draft_with_llm
from behaviordrafts.promotion import disable_behavior, promote_behavior
from behaviordrafts.reporting import write_json, write_jsonl
from behaviordrafts.runtime import EventSourcedRuntime
from behaviordrafts.sandbox import compile_runtime_behavior, run_behavior_sandbox
from behaviordrafts.static_analysis import run_static_analysis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.getenv("BEHAVIORDRAFTS_MODEL", DEFAULT_MODEL))
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--goal-limit", type=int, default=None)
    ap.add_argument("--goal-id", action="append", default=[])
    ap.add_argument("--no-promote", action="store_true")
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required for scripts/run_live_llm_matrix.py. Skipping live run.")
        return 2

    goals = json.loads(Path("experiments/live_llm_goals.json").read_text(encoding="utf-8"))
    for goal in goals:
        validate_matrix_goal(goal)
    if args.goal_id:
        goals = [g for g in goals if g["goal_id"] in set(args.goal_id)]
    if args.goal_limit:
        goals = goals[: args.goal_limit]

    cases, prompts, raws = [], [], []
    for goal in goals:
        for trial_idx in range(args.trials):
            runtime = EventSourcedRuntime()
            case = {"goal_id": goal["goal_id"], "trial_index": trial_idx, "model": args.model, "prompt_hash": None, "parsed_ok": False, "parse_error": None, "draft_created": False, "static_analysis_passed": False, "static_analysis_errors": [], "sandbox_created": False, "sandbox_passed": False, "source_compiled": False, "sandbox_executed_generated_source": False, "source_execution_error": None, "diff_match": False, "promotion_attempted": False, "promotion_succeeded": False, "matching_event_fired": False, "nonmatching_event_silent": False, "disable_succeeded": False, "behavior_silent_after_disable": False, "outcome": "failed", "failure_stage": "none", "errors": []}
            draft, meta = author_behavior_draft_with_llm(goal, {"condition": "C", "goal": goal["goal_id"]}, model=args.model)
            case["prompt_hash"] = meta.get("prompt_hash")
            case["parsed_ok"] = bool(meta.get("parsed_ok"))
            case["parse_error"] = meta.get("parse_error")
            if meta.get("draft_error"):
                case["errors"].append(meta.get("draft_error"))
            prompts.append({"goal_id": goal["goal_id"], "trial_index": trial_idx, "model": args.model, "prompt_hash": meta.get("prompt_hash"), "prompt": meta.get("prompt", "")})
            raws.append({"goal_id": goal["goal_id"], "trial_index": trial_idx, "model": args.model, "prompt_hash": meta.get("prompt_hash"), "raw_response": meta.get("raw_response", ""), "parse_error": meta.get("parse_error")})
            if draft is not None:
                case["draft_created"] = True
                analysis = run_static_analysis(draft)
                case["static_analysis_passed"] = analysis.analysis_passed
                case["static_analysis_errors"] = analysis.errors
                try:
                    trigger = Event("object.created", {"object": goal["trigger_object"]})
                    sandbox = run_behavior_sandbox(runtime, draft, None, trigger, author_behavior_tests(draft, goal), goal["budgets"], analysis_passed=analysis.analysis_passed)
                    case["sandbox_created"] = True
                    case["sandbox_passed"] = sandbox.sandbox_passed
                    case["source_compiled"] = sandbox.source_compiled
                    case["sandbox_executed_generated_source"] = sandbox.sandbox_executed_generated_source
                    case["source_execution_error"] = sandbox.source_execution_error
                    case["diff_match"] = sandbox.sandbox_passed and semantic_diff_matches(goal, sandbox.structural_diff)
                    if (not args.no_promote) and case["parsed_ok"] and case["static_analysis_passed"] and case["sandbox_passed"] and case["diff_match"]:
                        case["promotion_attempted"] = True
                        decision = promote_behavior(runtime, draft, analysis, sandbox, compile_runtime_behavior(draft.source_code))
                        case["promotion_succeeded"] = decision.decision == "approved"
                        if case["promotion_succeeded"]:
                            bid = next(iter(runtime.behaviors))
                            runtime.emit(trigger)
                            allowed = set(goal.get("allowed_object_types", []))
                            case["matching_event_fired"] = any(o.get("type") in allowed for o in runtime.graph.objects.values())
                            before = len(runtime.events)
                            runtime.emit(Event("object.created", {"object": {"id": "unrelated", "type": "Unrelated"}}))
                            case["nonmatching_event_silent"] = len(runtime.events) == before + 1
                            disable_behavior(runtime, bid)
                            case["disable_succeeded"] = not runtime.behaviors[bid].enabled
                            before2 = len(runtime.events)
                            runtime.emit(trigger)
                            case["behavior_silent_after_disable"] = len(runtime.events) == before2 + 1
                except Exception as exc:
                    case["errors"].append(f"test_construction_error: {exc}")
            case["failure_stage"] = assign_failure_stage(case)
            case["outcome"] = "passed" if case["failure_stage"] == "none" else "failed"
            cases.append(case)

    summary = aggregate_summary(cases, args.model, len(goals), args.trials)
    write_jsonl("results/live_llm_matrix_cases.jsonl", cases)
    write_jsonl("results/live_llm_matrix_prompts.jsonl", prompts)
    write_jsonl("results/live_llm_matrix_raw_responses.jsonl", raws)
    write_json("results/live_llm_matrix_summary.json", summary)
    Path("results/live_llm_matrix_summary.md").write_text(build_markdown(summary), encoding="utf-8")
    print("wrote live LLM matrix results to results/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
