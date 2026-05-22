import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib import request

from .drafts import BehaviorDraft

DEFAULT_MODEL = os.getenv("BEHAVIORDRAFTS_MODEL", "gpt-4o-mini")


def llm_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _build_prompt(goal: Dict[str, Any], fixture: Dict[str, Any]) -> str:
    return (
        "Author a single inert BehaviorDraft JSON object only.\\n"
        "Required keys: name, description, source_code, declared_trigger_events, declared_scope, declared_inputs, declared_outputs, "
        "declared_permissions, declared_dependencies, expected_emitted_events, expected_graph_mutations, tests.\\n"
        "Safety constraints:\\n"
        "- Do not import anything unless declared.\\n"
        "- Do not use filesystem, network, subprocess, eval, exec, open, compile, or dynamic import.\\n"
        "- Do not mutate global state.\\n"
        "- Do not register itself.\\n"
        "- Do not call promotion or guardrail code.\\n"
        "- Only read event and graph/context arguments.\\n"
        "- Only emit allowed graph objects/relations through context helper.\\n"
        "- Keep source code short and auditable.\\n"
        f"Goal: {json.dumps(goal, sort_keys=True)}\\n"
        f"Fixture baseline: {json.dumps(fixture, sort_keys=True)}"
    )


def _call_openai(prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {"format": {"type": "json_object"}},
    }
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body.get("output_text", "")


def author_behavior_draft_with_llm(goal: Dict[str, Any], fixture: Dict[str, Any], model: Optional[str] = None) -> Tuple[Optional[BehaviorDraft], Dict[str, Any]]:
    chosen_model = model or os.getenv("BEHAVIORDRAFTS_MODEL", DEFAULT_MODEL)
    prompt = _build_prompt(goal, fixture)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    meta: Dict[str, Any] = {
        "authoring_mode": "llm",
        "model": chosen_model,
        "prompt": prompt,
        "prompt_hash": prompt_hash,
        "raw_response": "",
        "parsed_ok": False,
        "parse_error": None,
        "created_at": now,
        "goal_id": goal.get("goal_name"),
        "condition": fixture.get("condition", "unknown"),
    }

    if not llm_available():
        meta["parse_error"] = "OPENAI_API_KEY missing"
        return None, meta

    try:
        raw = _call_openai(prompt, chosen_model, os.getenv("OPENAI_API_KEY", ""))
        meta["raw_response"] = raw
        payload = json.loads(raw)
        draft = BehaviorDraft(
            id=str(uuid.uuid4()),
            name=payload["name"],
            description=payload["description"],
            source_code=payload["source_code"],
            declared_trigger_events=payload.get("declared_trigger_events", ["object.created"]),
            declared_scope=payload.get("declared_scope", {}),
            declared_inputs=payload.get("declared_inputs", []),
            declared_outputs=payload.get("declared_outputs", []),
            declared_permissions=payload.get("declared_permissions", []),
            declared_dependencies=payload.get("declared_dependencies", []),
            expected_emitted_events=payload.get("expected_emitted_events", []),
            expected_graph_mutations=payload.get("expected_graph_mutations", {}),
            created_by="llm",
            created_from_goal=goal["goal_name"],
            model_used=chosen_model,
            prompt_hash=prompt_hash,
            authoring_mode="llm",
            provenance=meta,
            status="drafted",
        )
        meta["parsed_ok"] = True
        return draft, meta
    except Exception as exc:
        meta["parse_error"] = str(exc)
        return None, meta
