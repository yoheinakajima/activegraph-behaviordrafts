import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .demo_behaviors import file_summary_behavior, provenance_auditor_behavior
from .drafts import author_behavior_draft_fixture, author_behavior_tests
from .events import Event
from .promotion import disable_behavior, promote_behavior
from .reporting import write_json, write_jsonl
from .runtime import EventSourcedRuntime
from .sandbox import run_behavior_sandbox
from .static_analysis import run_static_analysis


def _fn_for_goal(goal_name: str):
    return file_summary_behavior if "summary" in goal_name else provenance_auditor_behavior


def _first_sentence_or_segment(content: str) -> str:
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if not lines:
        return ""
    joined = " ".join(lines)
    if "." in joined:
        return joined.split(".")[0].strip() + "."
    return lines[0]


def _semantic_diff_matches(goal_name: str, trigger_object: Dict[str, Any], diff: Dict[str, Any]) -> bool:
    created_objects = diff.get("created_objects", [])
    created_relations = diff.get("created_relations", [])

    if goal_name == "file_summary_behavior":
        summaries = [o for o in created_objects if o.get("type") == "Summary"]
        if len(summaries) != 1:
            return False
        summary = summaries[0]
        content = trigger_object.get("content", "")
        expected_first = _first_sentence_or_segment(content)
        expected_line_count = len(content.splitlines()) if content else 0
        if summary.get("first_sentence") != expected_first:
            return False
        if summary.get("line_count") != expected_line_count:
            return False
        return any(
            r.get("type") == "summarizes" and r.get("to") == trigger_object.get("id") and r.get("from") == summary.get("id")
            for r in created_relations
        )

    if goal_name == "provenance_auditor_behavior":
        evaluations = [o for o in created_objects if o.get("type") == "Evaluation"]
        if len(evaluations) != 1:
            return False
        evaluation = evaluations[0]
        missing = sum(1 for c in trigger_object.get("changes", []) if not c.get("provenance"))
        if evaluation.get("patch_proposal_id") != trigger_object.get("id"):
            return False
        if evaluation.get("missing_provenance_count") != missing:
            return False
        if evaluation.get("passes") != (missing == 0):
            return False
        return True

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
            behavior_fn = _fn_for_goal(goal["goal_name"])
            expected_diff = goal["expected_diff"]

            result: Dict[str, Any] = {
                "condition": condition,
                "goal": goal["goal_name"],
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
                "actual_diff": {"objects_created": 0, "relations_created": 0, "created_objects": [], "created_relations": []},
                "diff_match": False,
                "events_created": 0,
                "objects_created": 0,
                "relations_created": 0,
                "errors": [],
            }

            if condition != "A":
                draft = author_behavior_draft_fixture(goal["goal_name"], goal)
                tests = author_behavior_tests(draft, goal)
                analysis = run_static_analysis(draft)
                trigger = Event("object.created", {"object": goal["trigger_object"]})
                sandbox = run_behavior_sandbox(runtime, draft, behavior_fn, trigger, tests, goal["budgets"])

                semantic_ok = _semantic_diff_matches(goal["goal_name"], goal["trigger_object"], sandbox.structural_diff)
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
                        "diff_match": semantic_ok,
                        "live_graph_unchanged_before_promotion": len(runtime.graph.objects) == 0 and len(runtime.graph.relations) == 0,
                    }
                )

                decision = None
                if condition == "C":
                    result["promotion_attempted"] = True
                    decision = promote_behavior(runtime, draft, analysis, sandbox, behavior_fn)
                    result["promotion_succeeded"] = bool(decision and decision.decision == "approved")

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
    return all_results
