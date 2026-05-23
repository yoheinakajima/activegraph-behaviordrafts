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


def test_matrix_prompt_includes_summary_validator_schema_requirements():
    prompt = _build_prompt(_goal(), {"condition": "C", "goal": "file_summary_1"})
    assert 'Validator schema requirements (summary_validator):' in prompt
    assert 'type=\"Summary\", first_sentence, line_count' in prompt
    assert 'type=\"summarizes\", from=<summary id>, to=<source object id>' in prompt


def test_matrix_prompt_includes_todo_validator_schema_requirements():
    goal = {
        "goal_id": "todo_extract_1",
        "description": "Extract TODO lines.",
        "expected_objects": ["TodoFinding"],
        "expected_relations": [],
        "semantic_validator_type": "todo_extractor_validator",
    }
    prompt = _build_prompt(goal, {"condition": "C", "goal": "todo_extract_1"})
    assert 'Validator schema requirements (todo_extractor_validator):' in prompt
    assert 'type=\"TodoFinding\" per TODO line' in prompt
    assert 'Do not emit relations unless expected_relations is non-empty' in prompt


def test_matrix_prompt_includes_heading_validator_schema_requirements():
    goal = {
        "goal_id": "heading_count_1",
        "description": "Count headings.",
        "expected_objects": ["HeadingCount"],
        "expected_relations": [],
        "semantic_validator_type": "heading_count_validator",
    }
    prompt = _build_prompt(goal, {"condition": "C", "goal": "heading_count_1"})
    assert 'Validator schema requirements (heading_count_validator):' in prompt
    assert 'type=\"HeadingCount\", count, file_id' in prompt


def test_matrix_prompt_includes_fstring_quote_guidance():
    prompt = _build_prompt(_goal(), {"condition": "C", "goal": "file_summary_1"})
    assert "Avoid nested quotes inside f-strings" in prompt
    assert 'obj_id = obj["id"]' in prompt
    assert 'summary_id = f"summary-{obj_id}"' in prompt
    assert "Do not write: f'summary-{obj['id']}'" in prompt
