import argparse
import csv
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from run_eval import EVAL, RESULTS, SCENARIOS, load, quote_found, split

from referee.backends import ask, backend
from referee.retrieve import load_chunks
from referee.ruling import parse, with_penalties

JUDGE = "Groq / qwen/qwen3.8-27b"
SCORES = ["correct", "useful", "clear", "safe"]
PAUSE = 30
TRIES = 5


def system_prompt():
    rubric = (EVAL / "rubric.md").read_text(encoding="utf-8")
    return (
        (EVAL / "judge_prompt.md")
        .read_text(encoding="utf-8")
        .replace("{rubric}", rubric)
    )


def yes(value):
    return "yes" if value else "no"


def excerpts(row, s, chunks):
    pool = [c for c in chunks if c["id"] not in set(split(s["exclude"]))]
    by_id = {c["id"]: c for c in pool}
    cited = (row["ruling"] or {}).get("rules") or []
    wanted = {
        r.removeprefix("Rule ").strip()
        for r in [*cited, *split(s["rules"])]
        if isinstance(r, str)
    }
    found = with_penalties(
        [by_id[i] for i in row["retrieved"] if i in by_id and i in wanted], pool
    )
    return "\n\n".join(f"{c['id']}\n{c['text']}" for c in found) or "(none)"


def user_message(row, s, chunks):
    expected = {
        k: s[k]
        for k in ["type", "foul", "penalty_yards", "enforcement_spot", "rules"]
        if s[k]
    }
    return f"""Question: {s["question"]}

Expected answer: {s["answer"]}
Expected fields: {json.dumps(expected)}

App answer: {json.dumps(row["ruling"]) if row["ruling"] else row["raw"]}

Checks:
- Every cited rule was in the excerpts: {yes(not row["unverified"])}{f" (not found: {', '.join(row['unverified'])})" if row["unverified"] else ""}
- Quote found word for word: {yes(quote_found(row, s, chunks))}
- Flagged for review: {yes(row["needs_review"])}

Rulebook excerpts the app was given that it cited or the expected answer names:
{excerpts(row, s, chunks)}"""


def scores(text):
    verdict = parse((text or "").rsplit("</think>", 1)[-1])
    if not verdict or not all(verdict.get(k) in (1, 2, 3) for k in SCORES):
        return None
    return verdict


def judge(path, scenarios, chunks, label):
    out = RESULTS / f"judge_{path.stem}.jsonl"
    done = {r["id"] for r in load(out)}
    send = backend(label)
    system = system_prompt()
    with open(out, "a", encoding="utf-8") as f:
        for row in load(path):
            if row["run"] != 1 or row["id"] in done or row["id"] not in scenarios:
                continue
            messages = [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": user_message(row, scenarios[row["id"]], chunks),
                },
            ]
            for _ in range(TRIES):
                if (raw := ask(send, messages)) is not None:
                    break
                time.sleep(60)
            if raw is None:
                print(
                    f"  no answer for {row['id']}, stopping. Rerun later to continue."
                )
                return
            verdict = scores(raw)
            f.write(
                json.dumps(
                    {
                        "id": row["id"],
                        "model": row["model"],
                        "judge": label,
                        "raw": raw,
                        "verdict": verdict,
                    }
                )
                + "\n"
            )
            f.flush()
            print(f"  {row['id']}: {verdict and [verdict[k] for k in SCORES]}")
            time.sleep(PAUSE)


def compare(paths, sheet):
    with open(sheet, newline="", encoding="utf-8") as f:
        human = {(g["model"], g["id"]): g for g in csv.DictReader(f)}
    pairs = [
        (human[(j["model"], j["id"])], j["verdict"])
        for path in paths
        for j in load(RESULTS / f"judge_{path.stem}.jsonl")
        if j["verdict"] and human.get((j["model"], j["id"]), {}).get("correct")
    ]
    print(f"{len(pairs)} answers scored by both")
    print("| Item | same score | within 1 | human mean | judge mean |")
    print("|---|---|---|---|---|")
    for k in SCORES:
        h = [int(g[k]) for g, _ in pairs]
        j = [v[k] for _, v in pairs]
        same = sum(a == b for a, b in zip(h, j))
        near = sum(abs(a - b) <= 1 for a, b in zip(h, j))
        n = len(pairs) or 1
        print(
            f"| {k} | {same}/{len(pairs)} | {near}/{len(pairs)} | {sum(h) / n:.2f} | {sum(j) / n:.2f} |"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+", type=Path, help="eval/results/*.jsonl")
    parser.add_argument("--judge", default=JUDGE)
    parser.add_argument(
        "--compare",
        type=Path,
        help="grading sheet with Timothy's scores; only compares, no judge calls",
    )
    args = parser.parse_args()
    if args.compare:
        compare(args.results, args.compare)
        return
    load_dotenv()
    with open(SCENARIOS, newline="", encoding="utf-8") as f:
        scenarios = {s["id"]: s for s in csv.DictReader(f)}
    chunks = load_chunks()
    for path in args.results:
        judge(path, scenarios, chunks, args.judge)


if __name__ == "__main__":
    main()
