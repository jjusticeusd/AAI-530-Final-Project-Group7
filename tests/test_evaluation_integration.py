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

    def test_approved_human_grades_are_valid_and_separate_from_suggestions(self):
        with (ROOT / "eval/grading/v2_suggested_review.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 53)
        for row in rows:
            self.assertEqual(row["review_status"], "approved_by_timothy")
            self.assertTrue(
                all(
                    row[k] in {"1", "2", "3"}
                    for k in ["correct", "useful", "clear", "safe"]
                )
            )
        groq_d03 = next(
            row
            for row in rows
            if row["id"] == "d03" and row["model"].startswith("Groq /")
        )
        self.assertEqual(
            [groq_d03[k] for k in ["correct", "useful", "clear", "safe"]],
            ["1", "1", "1", "2"],
        )
        self.assertNotEqual(groq_d03["clear"], groq_d03["suggested_clear"])

    def test_final_grading_sheet_matches_user_approved_review(self):
        def load(name):
            with (ROOT / name).open(newline="") as f:
                return {(row["model"], row["id"]): row for row in csv.DictReader(f)}

        review = load("eval/grading/v2_suggested_review.csv")
        final = load("eval/results/v2_rag_dev_grading.csv")
        self.assertEqual(set(review), set(final))
        for key in final:
            self.assertEqual(
                [final[key][k] for k in ["correct", "useful", "clear", "safe"]],
                [review[key][k] for k in ["correct", "useful", "clear", "safe"]],
            )
        v1 = load("eval/results/v1_rag_dev_grading.csv")
        self.assertEqual(len(v1), 48)
        self.assertTrue(
            all(
                not any(row[k] for k in ["correct", "useful", "clear", "safe"])
                for row in v1.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
