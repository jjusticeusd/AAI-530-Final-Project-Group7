"""Adapt Timothy's approved JSONL cases to the current runner; no model calls."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "eval/scenarios_timothy.csv"
FIELDS = [
    "id",
    "split",
    "type",
    "question",
    "foul",
    "penalty_yards",
    "enforcement_spot",
    "rules",
    "exclude",
    "needs_review",
    "answer",
    "expected_behavior",
    "expected_enforcement",
    "review_status",
    "source_pages",
]


def adapted(case):
    """Keep question/answer text and IDs exact; label schema adaptations separately."""
    is_rule = case["id"] in {
        "NCAA-009",
        "NCAA-010",
        "NCAA-011",
        "NCAA-012",
        "NCAA-028",
        "NCAA-031",
        "NCAA-033",
        "NCAA-034",
        "NCAA-036",
    }
    kind = (
        "out_of_scope"
        if case["expected_behavior"] == "out_of_scope"
        else "rule"
        if is_rule
        else "play"
    )
    spot = ""
    if case["expected_foul"] is True:
        text = case["expected_enforcement"].lower()
        if case["category"] in {"false_start", "delay"}:
            spot = "succeeding spot"
        elif "previous spot" in text:
            spot = "previous spot"
        elif "foul spot" in text:
            spot = "spot of the foul"

    def value(v):
        return "" if v is None else str(v).lower()

    return {
        "id": case["id"],
        "split": case["split"],
        "type": kind,
        "question": case["question"],
        "foul": value(case["expected_foul"]),
        "penalty_yards": value(case["expected_penalty_yards"]),
        "enforcement_spot": spot,
        "rules": ";".join(case["rule_ids"]),
        # Exclude matching interpretation groups, retaining the underlying rules.
        "exclude": ";".join("A.R. " + r for r in case["rule_ids"]),
        "needs_review": value(case.get("expected_needs_review")),
        "answer": case["expected_answer"],
        "expected_behavior": case["expected_behavior"],
        "expected_enforcement": case["expected_enforcement"],
        "review_status": case["review_status"],
        "source_pages": json.dumps(case["source_pages"], ensure_ascii=False),
    }


def main():
    cases = []
    for split in ("dev", "test"):
        path = ROOT / f"evaluation/eval/{split}_scenarios.jsonl"
        cases.extend(json.loads(line) for line in path.read_text().splitlines())
    manifest = json.loads((ROOT / "evaluation/eval/split_manifest.json").read_text())
    assert len(cases) == 40 and len({c["id"] for c in cases}) == 40
    assert {c["id"] for c in cases if c["split"] == "test"} == set(manifest["test_ids"])
    assert all(c["review_status"] == "approved_by_timothy" for c in cases)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(adapted(c) for c in cases)
    print(
        "Adapted 40 approved cases: 30 development, 10 final test. Legacy scenarios unchanged."
    )


if __name__ == "__main__":
    main()
