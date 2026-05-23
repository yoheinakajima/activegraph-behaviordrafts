import json

from behaviordrafts.harness import run_experiments
from behaviordrafts.llm_author import _extract_response_text, author_behavior_draft_with_llm


def test_extract_response_text_from_output_array_shape():
    body = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": '{"name":"x"}'},
                ],
            }
        ]
    }
    assert _extract_response_text(body) == '{"name":"x"}'


def test_valid_llm_json_becomes_draft(monkeypatch):
    payload = {
        "name": "x",
        "description": "d",
        "source_code": "def behavior(event, graph, ctx):\n pass",
        "declared_trigger_events": ["object.created"],
        "declared_scope": {},
        "declared_inputs": [],
        "declared_outputs": [],
        "declared_permissions": [],
        "declared_dependencies": [],
        "expected_emitted_events": [],
        "expected_graph_mutations": {},
        "tests": [],
    }
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("behaviordrafts.llm_author._call_openai", lambda *args, **kwargs: json.dumps(payload))
    draft, meta = author_behavior_draft_with_llm({"goal_name": "g"}, {"condition": "C"})
    assert draft is not None
    assert draft.authoring_mode == "llm"
    assert meta["parsed_ok"]


def test_malformed_llm_json_records_parse_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("behaviordrafts.llm_author._call_openai", lambda *args, **kwargs: "{not-json")
    draft, meta = author_behavior_draft_with_llm({"goal_name": "g"}, {"condition": "C"})
    assert draft is None
    assert not meta["parsed_ok"]
    assert meta["parse_error"]


def test_llm_unsafe_code_fails_static_and_no_promotion(monkeypatch):
    payload = {
        "name": "x",
        "description": "d",
        "source_code": "def behavior(event, graph, ctx):\n eval('1')",
    }
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("behaviordrafts.llm_author._call_openai", lambda *args, **kwargs: json.dumps(payload))
    results = run_experiments(use_llm=True)
    c_rows = [r for r in results if r["condition"] == "C"]
    assert all(not r["static_analysis_passed"] for r in c_rows)
    assert all(not r["promotion_succeeded"] for r in c_rows)


def test_llm_mode_records_prompt_model_hash(monkeypatch):
    payload = {
        "name": "x",
        "description": "d",
        "source_code": "def behavior(event, graph, ctx):\n pass",
    }
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("BEHAVIORDRAFTS_MODEL", "gpt-test")
    monkeypatch.setattr("behaviordrafts.llm_author._call_openai", lambda *args, **kwargs: json.dumps(payload))
    run_experiments(use_llm=True)
    rows = [json.loads(line) for line in open("results/llm_prompts.jsonl", encoding="utf-8")]
    assert rows
    assert all(r["model"] == "gpt-test" for r in rows)
    assert all(r["prompt_hash"] for r in rows)
