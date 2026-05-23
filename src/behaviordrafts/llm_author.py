import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib import request

from .drafts import BehaviorDraft, get_goal_name

DEFAULT_MODEL = os.getenv("BEHAVIORDRAFTS_MODEL", "gpt-4o-mini")


def _extract_response_text(body: Dict[str, Any]) -> str:
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in body.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text
    return ""


def _extract_json_object_text(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty raw_response")
    if text.startswith("```"):
        parts = text.split("```")
        for chunk in parts:
            c = chunk.strip()
            if not c:
                continue
            if c.lower().startswith("json"):
                c = c[4:].strip()
            if c.startswith("{") and c.endswith("}"):
                return c
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object found in raw_response")
    depth = 0
    in_str = False
    escape = False
    end = -1
    for i, ch in enumerate(text[start:], start=start):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError("unterminated JSON object in raw_response")
    return text[start:end + 1]


def llm_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _build_prompt(goal: Dict[str, Any], fixture: Dict[str, Any]) -> str:
    return (
        "Author a single inert BehaviorDraft JSON object only.\\n"
        "Required keys: name, description, source_code, declared_trigger_events, declared_scope, declared_inputs, declared_outputs, "
        "declared_permissions, declared_dependencies, expected_emitted_events, expected_graph_mutations, tests.\\n"
        "Safety constraints:\\n"
        "- source_code must define exactly one callable: def behavior(event, graph, ctx):\\n"
        "- event is a wrapper dict (not an Event class) shaped as {\"object\": <trigger_object_dict>}.\\n"
        "- Always start by extracting the trigger object: obj = event[\"object\"].\\n"
        "- Read trigger fields from obj, never directly from event.\\n"
        "- Incorrect: content = event[\"content\"]\\n"
        "- Correct: obj = event[\"object\"]; content = obj.get(\"content\", \"\")\\n"
        "- emit with ctx.emit_object_created(obj) and ctx.emit_relation_created(rel) only.\\n"
        "- Objects passed to ctx.emit_object_created(obj) must be dicts with at least keys: id, type.\\n"
        "- Relations passed to ctx.emit_relation_created(rel) must be dicts with keys: type, from, to.\\n"
        "- Do not import anything unless declared.\\n"
        "- Do not use filesystem, network, subprocess, eval, exec, open, compile, or dynamic import.\\n"
        "- Do not mutate global state.\\n"
        "- Do not register itself.\\n"
        "- Do not call promotion or guardrail code.\\n"
        "- Only read event and graph/context arguments.\\n"
        "- Only emit allowed graph objects/relations through context helper.\\n"
        "- Keep source code short and auditable.\\n"
        "- Return strict JSON only (no markdown fences, no prose).\\n"
        "- Minimal summary pattern:\\n"
        "  obj = event[\"object\"]; content = obj.get(\"content\", \"\")\\n"
        "  ctx.emit_object_created({\"id\": f\"summary-{obj['id']}\", \"type\": \"Summary\"})\\n"
        "  ctx.emit_relation_created({\"type\": \"summarizes\", \"from\": f\"summary-{obj['id']}\", \"to\": obj[\"id\"]})\\n"
        "- Minimal object-only pattern:\\n"
        "  obj = event[\"object\"]\\n"
        "  ctx.emit_object_created({\"id\": f\"warning-{obj['id']}\", \"type\": \"Warning\"})\\n"
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
    return _extract_response_text(body)


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
        "goal_id": goal.get("goal_name") or goal.get("goal_id"),
        "condition": fixture.get("condition", "unknown"),
        "draft_error": None,
    }

    if not llm_available():
        meta["parse_error"] = "OPENAI_API_KEY missing"
        return None, meta

    try:
        raw = _call_openai(prompt, chosen_model, os.getenv("OPENAI_API_KEY", ""))
        meta["raw_response"] = raw
        json_text = _extract_json_object_text(raw)
        payload = json.loads(json_text)
        meta["parsed_ok"] = True
        goal_name = get_goal_name(goal)
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
            created_from_goal=goal_name,
            model_used=chosen_model,
            prompt_hash=prompt_hash,
            authoring_mode="llm",
            provenance=meta,
            status="drafted",
        )
        return draft, meta
    except (json.JSONDecodeError, ValueError) as exc:
        meta["parse_error"] = str(exc)
        return None, meta
    except Exception as exc:
        message = str(exc)
        meta["draft_error"] = message
        if not meta.get("parsed_ok") and not meta.get("parse_error"):
            meta["parse_error"] = f"llm_call_error: {message}"
        return None, meta
