import csv
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "approved", ROOT / "eval/approved_cases.py"
)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class IntegrationChecks(unittest.TestCase):
    def test_approved_cases_preserve_questions_answers_and_holdout(self):
        source = []
        for split in ["dev", "test"]:
            source.extend(
                json.loads(line)
                for line in (ROOT / f"evaluation/eval/{split}_scenarios.jsonl")
                .read_text()
                .splitlines()
            )
        with (ROOT / "eval/scenarios_timothy.csv").open(newline="") as f:
            converted = list(csv.DictReader(f))
        originals = {c["id"]: c for c in source}
        self.assertEqual(len(converted), 40)
        self.assertEqual(sum(c["split"] == "dev" for c in converted), 30)
        self.assertEqual(sum(c["split"] == "test" for c in converted), 10)
        for c in converted:
            original = originals[c["id"]]
            self.assertEqual(c["question"], original["question"])
            self.assertEqual(c["answer"], original["expected_answer"])
            self.assertEqual(c["split"], original["split"])
            self.assertEqual(
                c["expected_enforcement"], original["expected_enforcement"]
            )
            self.assertEqual(
                c["exclude"], ";".join("A.R. " + x for x in original["rule_ids"])
            )

    def test_legacy_ids_do_not_overlap_approved_ids(self):
        with (ROOT / "eval/scenarios.csv").open(newline="") as f:
            legacy = list(csv.DictReader(f))
        with (ROOT / "eval/scenarios_timothy.csv").open(newline="") as f:
            approved = list(csv.DictReader(f))
        self.assertEqual(len(legacy), 24)
        self.assertTrue({c["id"] for c in legacy}.isdisjoint(c["id"] for c in approved))

    def test_suggestions_do_not_become_human_grades(self):
        with (ROOT / "eval/grading/v2_suggested_review.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 53)
        for c in rows:
            self.assertEqual(c["review_status"], "pending_timothy_approval")
            self.assertTrue(
                all(c[k] == "" for k in ["correct", "useful", "clear", "safe"])
            )
            self.assertTrue(
                all(
                    int(c[k]) in (1, 2, 3)
                    for k in [
                        "suggested_correct",
                        "suggested_useful",
                        "suggested_clear",
                        "suggested_safe",
                    ]
                )
            )

    def test_old_grading_sheets_unchanged_and_blank(self):
        for name, count in [
            ("v1_rag_dev_grading.csv", 48),
            ("v2_rag_dev_grading.csv", 53),
        ]:
            with (ROOT / "eval/results" / name).open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), count)
            self.assertTrue(
                all(
                    not any(c[k] for k in ["correct", "useful", "clear", "safe"])
                    for c in rows
                )
            )


if __name__ == "__main__":
    unittest.main()
