import ast
from dataclasses import dataclass
from typing import List
import uuid

FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}
FORBIDDEN_IMPORTS = {"subprocess", "socket", "requests"}
FORBIDDEN_NAMES = {"promotion", "approval_policy", "guardrail"}
FORBIDDEN_GRAPH_CALLS = {"add_object", "add_relation", "clear", "update", "append"}
FORBIDDEN_ROOTS = {"runtime", "promotion", "guardrail"}


@dataclass
class StaticAnalysisReport:
    id: str
    draft_id: str
    syntax_ok: bool
    imports: List[str]
    forbidden_imports: List[str]
    forbidden_calls: List[str]
    filesystem_access_detected: bool
    network_access_detected: bool
    subprocess_detected: bool
    eval_exec_detected: bool
    undeclared_dependencies: List[str]
    permission_violations: List[str]
    analysis_passed: bool
    errors: List[str]


def run_static_analysis(draft):
    errors = []
    imports = []
    forbidden_imports = []
    forbidden_calls = []
    names = set()
    permission_violations = []
    try:
        tree = ast.parse(draft.source_code)
        syntax_ok = True
    except SyntaxError as e:
        return StaticAnalysisReport(str(uuid.uuid4()), draft.id, False, [], [], [], False, False, False, False, [], [], False, [str(e)])

    behavior_signature_ok = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "behavior":
            behavior_signature_ok = len(node.args.args) == 3
        if isinstance(node, ast.Import):
            for n in node.names:
                mod = n.name.split(".")[0]
                imports.append(mod)
                if mod in FORBIDDEN_IMPORTS:
                    forbidden_imports.append(mod)
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module.split(".")[0]
            imports.append(mod)
            if mod in FORBIDDEN_IMPORTS:
                forbidden_imports.append(mod)
        if isinstance(node, ast.Call):
            fn = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fn in FORBIDDEN_CALLS:
                forbidden_calls.append(fn)
        if isinstance(node, ast.Name):
            names.add(node.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            root = node.value.id
            attr = node.attr
            if root in FORBIDDEN_ROOTS:
                permission_violations.append(f"{root}.{attr}")
            if root == "ctx" and attr in {"runtime", "graph", "log", "promotion", "guardrails", "bindings", "__dict__"}:
                permission_violations.append(f"ctx.{attr}")
            if root == "graph" and attr in {"__dict__", "objects", "relations"}:
                permission_violations.append(f"graph.{attr}")
            if root == "graph" and attr in {"events", "behaviors", "bindings", "policies", "promotion", "guardrails"}:
                permission_violations.append(f"graph.{attr}")
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "graph":
                    permission_violations.append("graph attribute assignment")
                if isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Attribute) and isinstance(target.value.value, ast.Name) and target.value.value.id == "graph":
                        permission_violations.append(f"graph.{target.value.attr} subscript assignment")
        if isinstance(node, ast.Call):
            fn = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fn in {"setattr", "delattr"}:
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in {"graph", "ctx"}:
                    permission_violations.append(f"{fn}({node.args[0].id}, ...)")
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                if node.func.value.value.id == "graph" and node.func.attr in FORBIDDEN_GRAPH_CALLS:
                    permission_violations.append(f"graph.{node.func.value.attr}.{node.func.attr}(...)")

    undeclared = [i for i in imports if i not in draft.declared_dependencies and i not in {"typing"}]
    permission_violations.extend([n for n in names if n in FORBIDDEN_NAMES])
    analysis_passed = syntax_ok and behavior_signature_ok and not forbidden_imports and not forbidden_calls and not undeclared and not permission_violations
    if not behavior_signature_ok:
        errors.append("behavior function with signature (event, graph, ctx) is required")
    return StaticAnalysisReport(str(uuid.uuid4()), draft.id, syntax_ok, sorted(set(imports)), sorted(set(forbidden_imports)),
                                sorted(set(forbidden_calls)), "open" in forbidden_calls, bool(forbidden_imports),
                                "subprocess" in forbidden_imports, any(x in forbidden_calls for x in ["eval", "exec", "compile"]),
                                sorted(set(undeclared)), sorted(set(permission_violations)), analysis_passed, errors)
