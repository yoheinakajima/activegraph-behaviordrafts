import json
from pathlib import Path


def _load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    out = ["# Paper Tables", ""]
    summary = _load_json("results/summary.json")
    if summary is not None:
        out += ["## Table 1: Deterministic Lifecycle Summary", "", f"Runs: {len(summary)}", ""]

    live = _load_json("results/live_llm_summary.json")
    if live is None:
        out += ["## Table 5: Live LLM Authorship Run", "", "Live LLM results not present.", ""]
    else:
        failure_notes = []
        for key in ["parse_failures", "static_failures", "sandbox_failures", "semantic_failures"]:
            if live.get(key, 0):
                failure_notes.append(f"{key}={live[key]}")
        notes = "; ".join(failure_notes) if failure_notes else "none"
        out += [
            "## Table 5: Live LLM Authorship Run", "",
            "| goals | model | parsed | static pass | sandbox pass | semantic diff pass | promotions | matching fires | disable success | failure notes |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
            f"| {live.get('total_goals', 0)} | {live.get('model', '')} | {live.get('parsed_ok', 0)} | {live.get('static_analysis_passed', 0)} | {live.get('sandbox_passed', 0)} | {live.get('diff_matches', 0)} | {live.get('promotions_succeeded', 0)} | {live.get('matching_event_fires', 0)} | {live.get('disable_succeeded', 0)} | {notes} |",
            "",
        ]

    Path("results/paper_tables.md").write_text("\n".join(out), encoding="utf-8")
    print("wrote results/paper_tables.md")


if __name__ == "__main__":
    main()
