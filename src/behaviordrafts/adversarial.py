from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from .drafts import author_behavior_draft_fixture, author_behavior_tests
from .events import Event
from .harness import _semantic_diff_matches
from .promotion import promote_behavior
from .reporting import write_json, write_jsonl
from .runtime import EventSourcedRuntime
from .sandbox import compile_runtime_behavior, run_behavior_sandbox
from .static_analysis import run_static_analysis


@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    category: str
    goal_id: str
    source_code: str
    expected_static_pass: bool
    expected_sandbox_pass: bool
    expected_diff_match: bool
    expected_promotion_success: bool
    expected_live_graph_unchanged: bool


def _goal_map() -> Dict[str, Dict[str, Any]]:
    goals = json.loads(Path("experiments/goals.json").read_text(encoding="utf-8"))
    return {g["goal_name"]: g for g in goals}


def adversarial_cases() -> List[AdversarialCase]:
    fs = "file_summary_behavior"
    pa = "provenance_auditor_behavior"
    base = [
        ("uses_open", "static_reject", fs, "def behavior(event, graph, ctx):\n    open('/tmp/x')\n", False, False, False, False, True),
        ("uses_eval", "static_reject", fs, "def behavior(event, graph, ctx):\n    eval('1')\n", False, False, False, False, True),
        ("uses_exec", "static_reject", fs, "def behavior(event, graph, ctx):\n    exec('x=1')\n", False, False, False, False, True),
        ("uses_compile", "static_reject", fs, "def behavior(event, graph, ctx):\n    compile('1','x','eval')\n", False, False, False, False, True),
        ("imports_subprocess", "static_reject", fs, "import subprocess\ndef behavior(event, graph, ctx):\n    pass\n", False, False, False, False, True),
        ("imports_socket", "static_reject", fs, "import socket\ndef behavior(event, graph, ctx):\n    pass\n", False, False, False, False, True),
        ("uses_dunder_import", "static_reject", fs, "def behavior(event, graph, ctx):\n    __import__('os')\n", False, False, False, False, True),
        ("references_guardrail_names", "static_reject", fs, "def behavior(event, graph, ctx):\n    return guardrail\n", False, False, False, False, True),
        ("wrong_interface_run", "static_reject", fs, "def run(event, graph, ctx):\n    pass\n", False, False, False, False, True),
        ("wrong_behavior_args", "static_reject", fs, "def behavior(event):\n    pass\n", False, False, False, False, True),
        ("too_many_objects", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    for i in range(6):\n        ctx.emit_object_created({'id':f's{i}','type':'Summary','first_sentence':'x.','line_count':1})\n", True, False, False, False, True),
        ("too_many_relations", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    sid=f\"summary-{o['id']}\"\n    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'x.','line_count':1})\n    for i in range(5):\n        ctx.emit_relation_created({'type':'summarizes','from':sid,'to':o['id']})\n", True, False, False, False, True),
        ("disallowed_object_type", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    ctx.emit_object_created({'id':'x','type':'NotAllowed'})\n", True, False, False, False, True),
        ("disallowed_relation_type", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    sid=f\"summary-{o['id']}\"\n    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'x.','line_count':1})\n    ctx.emit_relation_created({'type':'links','from':sid,'to':o['id']})\n", True, False, False, False, True),
        ("raises_exception", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    raise RuntimeError('boom')\n", True, False, False, False, True),
        ("mutates_graph_directly", "sandbox_reject", fs, "def behavior(event, graph, ctx):\n    graph.objects['x']={'id':'x','type':'Summary'}\n", True, True, False, False, True),
        ("summary_wrong_line_count", "semantic_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    sid=f\"summary-{o['id']}\"\n    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'First sentence.','line_count':999})\n    ctx.emit_relation_created({'type':'summarizes','from':sid,'to':o['id']})\n", True, True, False, False, True),
        ("summary_missing_relation", "semantic_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    sid=f\"summary-{o['id']}\"\n    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'First sentence.','line_count':2})\n", True, True, False, False, True),
        ("summary_wrong_first_sentence", "semantic_reject", fs, "def behavior(event, graph, ctx):\n    o=event['object']\n    sid=f\"summary-{o['id']}\"\n    ctx.emit_object_created({'id':sid,'type':'Summary','first_sentence':'Wrong.','line_count':2})\n    ctx.emit_relation_created({'type':'summarizes','from':sid,'to':o['id']})\n", True, True, False, False, True),
        ("provenance_missing_patch_id", "semantic_reject", pa, "def behavior(event, graph, ctx):\n    o=event['object']\n    ctx.emit_object_created({'id':f\"eval-{o['id']}\",'type':'Evaluation','passes':False,'missing_provenance_count':1})\n", True, True, False, False, True),
        ("provenance_wrong_missing_count", "semantic_reject", pa, "def behavior(event, graph, ctx):\n    o=event['object']\n    ctx.emit_object_created({'id':f\"eval-{o['id']}\",'type':'Evaluation','patch_proposal_id':o['id'],'passes':False,'missing_provenance_count':0})\n", True, True, False, False, True),
        ("provenance_wrong_pass_fail", "semantic_reject", pa, "def behavior(event, graph, ctx):\n    o=event['object']\n    ctx.emit_object_created({'id':f\"eval-{o['id']}\",'type':'Evaluation','patch_proposal_id':o['id'],'passes':True,'missing_provenance_count':1})\n", True, True, False, False, True),
        ("control_valid_file_summary", "benign_control", fs, _goal_map()[fs]["source_code"], True, True, True, True, True),
        ("control_valid_provenance", "benign_control", pa, _goal_map()[pa]["source_code"], True, True, True, True, True),
    ]
    return [AdversarialCase(*c) for c in base]


def run_adversarial_experiments() -> Dict[str, Any]:
    goals = _goal_map()
    rows: List[Dict[str, Any]] = []
    for case in adversarial_cases():
        goal = dict(goals[case.goal_id])
        goal["source_code"] = case.source_code
        runtime = EventSourcedRuntime()
        draft = author_behavior_draft_fixture(case.case_id, goal)
        tests = author_behavior_tests(draft, goal)
        analysis = run_static_analysis(draft)
        sandbox_created = analysis.analysis_passed
        sandbox = run_behavior_sandbox(runtime, draft, None, Event("object.created", {"object": goal["trigger_object"]}), tests, goal["budgets"], analysis_passed=analysis.analysis_passed)
        diff_match = False
        if sandbox_created:
            diff_match = sandbox.sandbox_passed and _semantic_diff_matches(goal["goal_name"], goal["trigger_object"], sandbox.structural_diff)
        promotion_attempted = sandbox_created and sandbox.sandbox_passed and diff_match
        promotion_succeeded = False
        if promotion_attempted:
            decision = promote_behavior(runtime, draft, analysis, sandbox, compile_runtime_behavior(draft.source_code), approval_policy=True)
            promotion_succeeded = bool(decision and decision.decision == "approved")
        row = {
            "case_id": case.case_id,
            "category": case.category,
            "goal_id": case.goal_id,
            "static_analysis_passed": analysis.analysis_passed,
            "sandbox_created": sandbox_created,
            "sandbox_passed": sandbox.sandbox_passed if sandbox_created else False,
            "source_compiled": sandbox.source_compiled if sandbox_created else False,
            "sandbox_executed_generated_source": sandbox.sandbox_executed_generated_source if sandbox_created else False,
            "source_execution_error": sandbox.source_execution_error if sandbox_created else None,
            "diff_match": diff_match,
            "promotion_attempted": promotion_attempted,
            "promotion_succeeded": promotion_succeeded,
            "live_graph_unchanged": len(runtime.graph.objects) == 0 and len(runtime.graph.relations) == 0,
            "expected_static_pass": case.expected_static_pass,
            "expected_sandbox_pass": case.expected_sandbox_pass,
            "expected_diff_match": case.expected_diff_match,
            "expected_promotion_success": case.expected_promotion_success,
            "expected_live_graph_unchanged": case.expected_live_graph_unchanged,
            "errors": list(analysis.errors) + (sandbox.exceptions if sandbox_created else []),
        }
        row["outcome_matches_expectation"] = all([
            row["static_analysis_passed"] == row["expected_static_pass"],
            row["sandbox_passed"] == row["expected_sandbox_pass"],
            row["diff_match"] == row["expected_diff_match"],
            row["promotion_succeeded"] == row["expected_promotion_success"],
            row["live_graph_unchanged"] == row["expected_live_graph_unchanged"],
        ])
        rows.append(row)

    summary = {
        "total_cases": len(rows),
        "static_reject_cases": sum(1 for r in rows if r["category"] == "static_reject"),
        "sandbox_reject_cases": sum(1 for r in rows if r["category"] == "sandbox_reject"),
        "semantic_reject_cases": sum(1 for r in rows if r["category"] == "semantic_reject"),
        "benign_control_cases": sum(1 for r in rows if r["category"] == "benign_control"),
        "cases_matching_expectation": sum(1 for r in rows if r["outcome_matches_expectation"]),
        "unexpected_passes": sum(1 for r in rows if not r["outcome_matches_expectation"] and r["promotion_succeeded"]),
        "unexpected_failures": sum(1 for r in rows if not r["outcome_matches_expectation"] and not r["promotion_succeeded"]),
        "promotions_succeeded": sum(1 for r in rows if r["promotion_succeeded"]),
        "rejected_promotions": sum(1 for r in rows if not r["promotion_succeeded"]),
        "live_graph_violations": sum(1 for r in rows if not r["live_graph_unchanged"]),
    }

    write_json("results/adversarial_summary.json", summary)
    md = "# Adversarial Summary\n\n" + "\n".join(f"- {k}: {v}" for k, v in summary.items())
    write_jsonl("results/adversarial_cases.jsonl", rows)
    Path("results/adversarial_summary.md").write_text(md + "\n", encoding="utf-8")
    return {"summary": summary, "cases": rows}
