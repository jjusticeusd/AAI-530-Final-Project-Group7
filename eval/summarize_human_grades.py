"""Summarize explicit human grades and compare saved judge scores; no API calls."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = ["correct", "useful", "clear", "safe"]


def main():
    sheet = ROOT / "results/v2_rag_dev_grading.csv"
    with sheet.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 53 and all(
        all(row[k] in {"1", "2", "3"} for k in ITEMS) for row in rows
    )
    groups = defaultdict(list)
    for row in rows:
        groups[row["model"]].append(row)
    text = "# V2 human grading results\n\nTimothy approved grades for all 53 available run-1 answers on November 23, 2026. These answer Jason’s historical 18 development questions; they are not final-test scores or results on the separate approved 40-case dataset. Groq d16 has no response and is excluded, not assigned zero. No new model calls were made.\n\n"
    text += "## Human scores\n\nScores range from 1 to 3. Means are subjective rubric scores, not overall accuracy percentages. Full-credit correct counts require correct=3.\n\n| Model | Answers | Correct mean | Useful mean | Clear mean | Safe mean | Correct=3 |\n|---|---:|---:|---:|---:|---:|---:|\n"
    summary = []
    for model, group in sorted(groups.items()):
        means = {
            k: round(sum(int(row[k]) for row in group) / len(group), 3) for k in ITEMS
        }
        count = sum(row["correct"] == "3" for row in group)
        text += (
            f"| {model} | {len(group)} | "
            + " | ".join(f"{means[k]:.2f}" for k in ITEMS)
            + f" | {count}/{len(group)} |\n"
        )
        summary.append(
            {
                "model": model,
                "answers": len(group),
                "means": means,
                "full_credit_correct": count,
            }
        )
    human = {(row["model"], row["id"]): row for row in rows}
    pairs = []
    for path in sorted((ROOT / "results").glob("judge_v2_rag_*.jsonl")):
        for line in path.read_text().splitlines():
            record = json.loads(line)
            verdict = record.get("verdict")
            key = (record["model"], record["id"])
            if (
                key in human
                and isinstance(verdict, dict)
                and all(verdict.get(k) in {1, 2, 3} for k in ITEMS)
            ):
                pairs.append((human[key], verdict))
    assert len({(h["model"], h["id"]) for h, _ in pairs}) == len(pairs)
    text += "\n## Human versus saved LLM judge\n\nAll final human scores were supplied before this comparison. The AI-assisted suggestions were prepared without reading the saved judge scores; they were visible to Timothy, so these human ratings were assisted rather than fully blind independent ratings. The judge is a second opinion, not ground truth.\n\n| Criterion | Paired answers | Exact agreement | Within one point | Human mean | Judge mean |\n|---|---:|---:|---:|---:|---:|\n"
    agreement = {}
    for k in ITEMS:
        h = [int(a[k]) for a, _ in pairs]
        j = [b[k] for _, b in pairs]
        n = len(pairs)
        same = sum(a == b for a, b in zip(h, j))
        near = sum(abs(a - b) <= 1 for a, b in zip(h, j))
        agreement[k] = {
            "pairs": n,
            "same": same,
            "within_one": near,
            "human_mean": sum(h) / n if n else None,
            "judge_mean": sum(j) / n if n else None,
        }
        if n:
            text += f"| {k} | {n} | {same}/{n} | {near}/{n} | {sum(h) / n:.2f} | {sum(j) / n:.2f} |\n"
    text += "\n## Scope\n\nV1 human grading (48 saved answers) remains ungraded. These approved scores cover only v2 run 1, not all repeated runs. The 10 reserved final cases remain unused. Timothy resolved d08 against the pinned 2026 momentum exception: possession at own 3 followed by original momentum into the end zone returns the ball to the 3.\n"
    folder = ROOT / "grading"
    (folder / "V2_HUMAN_RESULTS.md").write_text(text, encoding="utf-8")
    (folder / "v2_human_summary.json").write_text(
        json.dumps(
            {
                "approved_answers": len(rows),
                "models": summary,
                "judge_agreement": agreement,
                "reserved_test_run": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "approved_answers": len(rows),
                "models": summary,
                "paired_judge_answers": len(pairs),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
