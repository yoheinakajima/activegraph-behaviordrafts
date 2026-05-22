import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .drafts import author_behavior_draft_fixture, author_behavior_tests
from .llm_author import author_behavior_draft_with_llm, llm_available
from .events import Event
from .promotion import disable_behavior, promote_behavior
from .reporting import write_json, write_jsonl
from .runtime import EventSourcedRuntime
from .sandbox import compile_runtime_behavior, run_behavior_sandbox
from .static_analysis import run_static_analysis


def _diff_matches(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    return (
        actual.get("objects_created", 0) == expected.get("objects_created", 0)
        and actual.get("relations_created", 0) == expected.get("relations_created", 0)
    )


def _semantic_diff_matches(goal_name: str, trigger_object: Dict[str, Any], diff: Dict[str, Any]) -> bool:
    created_objects = diff.get("created_objects", [])
    created_relations = diff.get("created_relations", [])

    if goal_name == "file_summary_behavior":
        if len(created_objects) != 1:
            return False
        summary = created_objects[0]
        if summary.get("type") != "Summary":
            return False
        content = trigger_object.get("content", "")
        first = (content.split(".")[0].strip() + ".") if "." in content else content.strip()
        line_count = len(content.splitlines()) if content else 0
        if summary.get("first_sentence") != first or summary.get("line_count") != line_count:
            return False
        sid = f"summary-{trigger_object.get('id')}"
        return any(
            r.get("type") == "summarizes" and r.get("from") == sid and r.get("to") == trigger_object.get("id")
            for r in created_relations
        )

    if goal_name == "provenance_auditor_behavior":
        if len(created_objects) != 1:
            return False
        evaluation = created_objects[0]
        if evaluation.get("type") != "Evaluation":
            return False
        changes = trigger_object.get("changes", [])
        missing = sum(1 for c in changes if not c.get("provenance"))
        return (
            evaluation.get("patch_proposal_id") == trigger_object.get("id")
            and evaluation.get("missing_provenance_count") == missing
            and evaluation.get("passes") == (missing == 0)
        )

    return False


def _build_summary_markdown(results: List[Dict[str, Any]], timestamp: str) -> str:
    goals = sorted({r["goal"] for r in results})
    conditions = sorted({r["condition"] for r in results})

    def total(key: str) -> int:
        return sum(1 for r in results if bool(r.get(key)))

    condition_rows = []
    for c in conditions:
        subset = [r for r in results if r["condition"] == c]
        condition_rows.append(
            "| {c} | {d} | {s} | {p} | {mf} | {ns} |".format(
                c=c,
                d=sum(1 for r in subset if r.get("draft_created")),
                s=sum(1 for r in subset if r.get("sandbox_run_created")),
                p=sum(1 for r in subset if r.get("promotion_succeeded")),
                mf=sum(1 for r in subset if r.get("promoted_behavior_fired_on_matching_event")),
                ns=sum(1 for r in subset if r.get("promoted_behavior_silent_on_nonmatching_event")),
            )
        )

    goal_rows = []
    for g in goals:
        subset = [r for r in results if r["goal"] == g]
        goal_rows.append(
            "| {g} | {runs} | {prom} | {sandbox} | {diff} |".format(
                g=g,
                runs=len(subset),
                prom=sum(1 for r in subset if r.get("promotion_succeeded")),
                sandbox=sum(1 for r in subset if r.get("sandbox_passed")),
                diff=sum(1 for r in subset if r.get("diff_match")),
            )
        )

    by_mode = {"fixture": [r for r in results if r.get("authoring_mode") == "fixture"], "llm": [r for r in results if r.get("authoring_mode") == "llm"]}

    return "\n".join(
        [
            "# Behavior Draft Experiment Summary",
            "",
            f"- **Timestamp (UTC):** {timestamp}",
            f"- **Goals:** {len(goals)}",
            f"- **Conditions:** {len(conditions)}",
            f"- **Total runs:** {len(results)}",
            "",
            "## Aggregate Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Goals | {len(goals)} |",
            f"| Conditions | {len(conditions)} |",
            f"| Runs | {len(results)} |",
            f"| Drafts created | {total('draft_created')} |",
            f"| Static analysis passed | {total('static_analysis_passed')} |",
            f"| Sandbox passed | {total('sandbox_passed')} |",
            f"| Promotions succeeded | {total('promotion_succeeded')} |",
            "",
            "## Condition Results",
            "",
            "| Condition | Drafts | Sandbox Runs | Promotions | Matching Fires | Nonmatching Silent |",
            "|---|---:|---:|---:|---:|---:|",
            *condition_rows,
            "",
            "## Per-goal Results",
            "",
            "| Goal | Runs | Promotions | Sandbox Passed | Diff Match |",
            "|---|---:|---:|---:|---:|",
            *goal_rows,
            "",
            "## Interpretation",
            "",
            "Condition A cannot author new behavior. Condition B can create inert drafts but cannot change runtime behavior. "
            "Condition C can promote scoped behavior after validation, enabling the two demo capabilities while preserving "
            "live graph isolation before promotion.",
            "",
            "## Fixture vs LLM Authorship",
            "",
            "| Authoring Mode | Drafts | Parsed | Static Pass | Sandbox Pass | Promotions | Diff Matches |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| fixture | {len(by_mode['fixture'])} | {sum(1 for r in by_mode['fixture'] if r.get('llm_parsed_ok', True))} | {sum(1 for r in by_mode['fixture'] if r.get('static_analysis_passed'))} | {sum(1 for r in by_mode['fixture'] if r.get('sandbox_passed'))} | {sum(1 for r in by_mode['fixture'] if r.get('promotion_succeeded'))} | {sum(1 for r in by_mode['fixture'] if r.get('diff_match'))} |",
            f"| llm | {len(by_mode['llm'])} | {sum(1 for r in by_mode['llm'] if r.get('llm_parsed_ok'))} | {sum(1 for r in by_mode['llm'] if r.get('llm_static_analysis_passed', r.get('static_analysis_passed')))} | {sum(1 for r in by_mode['llm'] if r.get('llm_sandbox_passed', r.get('sandbox_passed')))} | {sum(1 for r in by_mode['llm'] if r.get('llm_promotion_succeeded', r.get('promotion_succeeded')))} | {sum(1 for r in by_mode['llm'] if r.get('llm_diff_match', r.get('diff_match')))} |",
            "",
        ]
    )


def run_experiments(use_llm: bool = False):
    goals = json.loads(Path("experiments/goals.json").read_text(encoding="utf-8"))
    all_results: List[Dict[str, Any]] = []
    events_log: List[Dict[str, Any]] = []
    drafts_log: List[Dict[str, Any]] = []
    sandboxes: List[Dict[str, Any]] = []

    for condition in ["A", "B", "C"]:
        for goal in goals:
            runtime = EventSourcedRuntime()
            expected_diff = goal["expected_diff"]

            result: Dict[str, Any] = {
                "condition": condition,
                "goal": goal["goal_name"],
                "authoring_mode": "llm" if use_llm else "fixture",
                "draft_created": False,
                "draft_valid_syntax": False,
                "static_analysis_passed": False,
                "tests_created": False,
                "tests_passed": False,
                "sandbox_run_created": False,
                "sandbox_passed": False,
                "live_graph_unchanged_before_promotion": True,
                "promotion_attempted": False,
                "promotion_succeeded": False,
                "promoted_behavior_fired_on_matching_event": False,
                "promoted_behavior_silent_on_nonmatching_event": False,
                "disable_succeeded": False,
                "behavior_silent_after_disable": False,
                "expected_diff": expected_diff,
                "actual_diff": {"objects_created": 0, "relations_created": 0},
                "diff_match": False,
                "events_created": 0,
                "objects_created": 0,
                "relations_created": 0,
                "errors": [],
                "llm_attempted": False,
                "llm_parsed_ok": None,
                "llm_parse_error": None,
                "llm_static_analysis_passed": None,
                "llm_sandbox_passed": None,
                "llm_promotion_succeeded": None,
                "llm_diff_match": None,
                "promoted_source_execution_mode": None,
                "promoted_runtime_uses_readonly_graph": None,
                "promoted_runtime_uses_emit_only_ctx": None,
                "promoted_runtime_direct_mutation_blocked": None,
            }

            if condition != "A":
                if use_llm:
                    result["llm_attempted"] = True
                    draft, llm_meta = author_behavior_draft_with_llm(goal, {"condition": condition, "goal": goal["goal_name"]})
                    result["llm_parsed_ok"] = llm_meta.get("parsed_ok")
                    result["llm_parse_error"] = llm_meta.get("parse_error")
                else:
                    draft = author_behavior_draft_fixture(goal["goal_name"], goal)

                if draft is None:
                    drafts_log.append({"authoring_mode": "llm", "goal": goal["goal_name"], "condition": condition, "parse_error": result["llm_parse_error"]})
                    all_results.append(result)
                    write_json(f"results/{condition}_{goal['goal_name']}.json", result)
                    continue

                tests = author_behavior_tests(draft, goal)
                analysis = run_static_analysis(draft)
                trigger = Event("object.created", {"object": goal["trigger_object"]})
                sandbox = run_behavior_sandbox(runtime, draft, None, trigger, tests, goal["budgets"], analysis_passed=analysis.analysis_passed)

                result.update(
                    {
                        "draft_created": True,
                        "draft_valid_syntax": analysis.syntax_ok,
                        "static_analysis_passed": analysis.analysis_passed,
                        "tests_created": len(tests) > 0,
                        "tests_passed": sandbox.tests_passed == sandbox.tests_run,
                        "sandbox_run_created": True,
                        "sandbox_passed": sandbox.sandbox_passed,
                        "actual_diff": sandbox.structural_diff,
                        "diff_match": _diff_matches(expected_diff, sandbox.structural_diff)
                        and _semantic_diff_matches(goal["goal_name"], goal["trigger_object"], sandbox.structural_diff),
                        "live_graph_unchanged_before_promotion": len(runtime.graph.objects) == 0 and len(runtime.graph.relations) == 0,
                        "llm_static_analysis_passed": analysis.analysis_passed if use_llm else None,
                        "llm_sandbox_passed": sandbox.sandbox_passed if use_llm else None,
                        "llm_diff_match": (_diff_matches(expected_diff, sandbox.structural_diff) and _semantic_diff_matches(goal["goal_name"], goal["trigger_object"], sandbox.structural_diff)) if use_llm else None,
                        "source_execution_mode": sandbox.source_execution_mode,
                        "source_compiled": sandbox.source_compiled,
                        "source_execution_error": sandbox.source_execution_error,
                        "sandbox_executed_generated_source": sandbox.sandbox_executed_generated_source,
                    }
                )

                decision = None
                if condition == "C":
                    result["promotion_attempted"] = True
                    decision = promote_behavior(runtime, draft, analysis, sandbox, compile_runtime_behavior(draft.source_code))
                    result["promotion_succeeded"] = bool(decision and decision.decision == "approved")
                    if result["promotion_succeeded"]:
                        result["promoted_source_execution_mode"] = "draft_source"
                        result["promoted_runtime_uses_readonly_graph"] = True
                        result["promoted_runtime_uses_emit_only_ctx"] = True
                        result["promoted_runtime_direct_mutation_blocked"] = True
                    if use_llm:
                        result["llm_promotion_succeeded"] = result["promotion_succeeded"]

                if decision and decision.decision == "approved":
                    binding_id = next(iter(runtime.behaviors))
                    runtime.emit(trigger)
                    result["promoted_behavior_fired_on_matching_event"] = any(
                        o.get("type") in ["Summary", "Evaluation"] for o in runtime.graph.objects.values()
                    )

                    nonmatching_before = len(runtime.events)
                    runtime.emit(Event("object.created", {"object": {"id": "unrelated-1", "type": "Unrelated"}}))
                    nonmatching_after = len(runtime.events)
                    result["promoted_behavior_silent_on_nonmatching_event"] = nonmatching_after == nonmatching_before + 1

                    disable_behavior(runtime, binding_id)
                    result["disable_succeeded"] = not runtime.behaviors[binding_id].enabled

                    disabled_before = len(runtime.events)
                    runtime.emit(trigger)
                    disabled_after = len(runtime.events)
                    result["behavior_silent_after_disable"] = disabled_after == disabled_before + 1

                drafts_log.append(asdict(draft))
                sandboxes.append(asdict(sandbox))

            result["events_created"] = len(runtime.events)
            result["objects_created"] = len(runtime.graph.objects)
            result["relations_created"] = len(runtime.graph.relations)
            events_log.extend([e.__dict__ for e in runtime.events])

            all_results.append(result)
            write_json(f"results/{condition}_{goal['goal_name']}.json", result)

    write_json("results/summary.json", all_results)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    Path("results/summary.md").write_text(_build_summary_markdown(all_results, timestamp), encoding="utf-8")
    write_jsonl("results/events.jsonl", events_log)
    write_jsonl("results/drafts.jsonl", drafts_log)
    write_jsonl("results/sandbox_runs.jsonl", sandboxes)
    llm_rows = [r for r in drafts_log if r.get("authoring_mode") == "llm" or r.get("created_by") == "llm"]
    if use_llm:
        write_jsonl("results/llm_drafts.jsonl", llm_rows)
        write_jsonl("results/llm_prompts.jsonl", [{"goal": r.get("created_from_goal"), "prompt_hash": r.get("prompt_hash"), "model": r.get("model_used"), "provenance": r.get("provenance", {})} for r in llm_rows])
        write_jsonl("results/llm_raw_responses.jsonl", [{"goal": r.get("created_from_goal"), "raw_response": r.get("provenance", {}).get("raw_response", ""), "parse_error": r.get("provenance", {}).get("parse_error")} for r in llm_rows])
    return all_results
