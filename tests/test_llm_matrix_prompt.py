from behaviordrafts.llm_author import _build_prompt


def _goal():
    return {
        "goal_id": "file_summary_1",
        "description": "Summarize file first sentence and line count.",
        "expected_objects": ["Summary"],
        "expected_relations": ["summarizes"],
        "semantic_validator_type": "summary_validator",
    }


def test_matrix_prompt_includes_event_wrapper_and_warning():
    prompt = _build_prompt(_goal(), {"condition": "C", "goal": "file_summary_1"})
    assert 'event is a wrapper dict' in prompt
    assert 'obj = event["object"]' in prompt
    assert 'Incorrect: content = event["content"]' in prompt or "Incorrect: content = event['content']" in prompt


def test_matrix_prompt_includes_ctx_emission_schema_requirements():
    prompt = _build_prompt(_goal(), {"condition": "C", "goal": "file_summary_1"})
    assert 'ctx.emit_object_created(obj)' in prompt
    assert 'at least keys: id, type' in prompt
    assert 'ctx.emit_relation_created(rel)' in prompt
    assert 'keys: type, from, to' in prompt


def test_matrix_prompt_includes_validator_specific_goal_fields():
    prompt = _build_prompt(_goal(), {"condition": "C", "goal": "file_summary_1"})
    assert '"semantic_validator_type": "summary_validator"' in prompt
    assert '"expected_objects": ["Summary"]' in prompt
    assert '"expected_relations": ["summarizes"]' in prompt
