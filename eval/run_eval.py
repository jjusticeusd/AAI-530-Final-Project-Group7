import argparse
import csv
import json
import re
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from referee.backends import ask, available, backend
from referee.retrieve import load_chunks
from referee.ruling import PROMPT, RULE_NUMBER, rule

EVAL = Path(__file__).parent
SCENARIOS = EVAL / "scenarios.csv"
RESULTS = EVAL / "results"
CHECKS = ["parsed", "type", "foul", "yards", "spot", "rule", "citations", "quote", "review"]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split(value):
    return [v.strip() for v in value.split(";") if v.strip()]


def numbers(rules):
    return {n for r in rules for n in RULE_NUMBER.findall(r)}


def score(s, result):
    r = result["ruling"]
    if r is None:
        return {"parsed": False}
    checks = {
        "parsed": True,
        "type": r.get("type") == s["type"],
        "citations": not result["unverified"],
        "quote": result["quote_found"],
    }
    if s["foul"]:
        checks["foul"] = r.get("foul") == (s["foul"] == "true")
    if s["penalty_yards"]:
        checks["yards"] = str(r.get("penalty_yards")) == s["penalty_yards"]
    if s["enforcement_spot"]:
        checks["spot"] = s["enforcement_spot"] in (r.get("enforcement_spot") or "").lower()
    if s["rules"]:
        cited = numbers(x for x in r.get("rules") or [] if isinstance(x, str))
        checks["rule"] = any(c == w or c.startswith(f"{w}-") for c in cited for w in numbers(split(s["rules"])))
    if s["needs_review"]:
        checks["review"] = result["needs_review"] == (s["needs_review"] == "true")
    return checks


def decision(result):
    r = result["ruling"] or {}
    return json.dumps([r.get("type"), r.get("foul"), r.get("penalty_yards"), (r.get("enforcement_spot") or "").lower()])


def load(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def run(label, scenarios, chunks, prompt, runs):
    path = RESULTS / f"{prompt}_{slug(label)}.jsonl"
    done = {(r["id"], r["run"]) for r in load(path)}
    send = backend(label)
    with open(path, "a", encoding="utf-8") as f:
        for s in scenarios:
            for n in range(1, runs + 1):
                if (s["id"], n) in done:
                    continue
                start = time.perf_counter()
                result = rule(chunks, lambda m: ask(send, m), [{"role": "user", "content": s["question"]}], prompt, set(split(s["exclude"])))
                seconds = round(time.perf_counter() - start, 2)
                if result["raw"] is None:
                    print(f"  {label}: no answer for {s['id']} run {n}, stopping. Rerun later to continue.")
                    return
                row = {"id": s["id"], "run": n, "model": label, "prompt": prompt, "seconds": seconds, "retrieved": result["retrieved"],
                       "raw": result["raw"], "ruling": result["ruling"], "unverified": result["unverified"],
                       "quote_found": result["quote_found"], "needs_review": result["needs_review"], "checks": score(s, result)}
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"  {label} {s['id']} run {n}: {seconds}s {'ok' if all(row['checks'].values()) else 'miss'}")


def rate(values):
    return f"{sum(values)}/{len(values)}" if values else "-"


def summarize(prompt, name, ids):
    lines = ["| Model | " + " | ".join(CHECKS) + " | consistent | median s |", "|" + "---|" * (len(CHECKS) + 3)]
    grading = []
    for path in sorted(RESULTS.glob(f"{prompt}_*.jsonl")):
        rows = [r for r in load(path) if r["id"] in ids]
        if not rows:
            continue
        by_id = defaultdict(list)
        for r in rows:
            by_id[r["id"]].append(r)
        cells = [rate([r["checks"][c] for r in rows if c in r["checks"]]) for c in CHECKS]
        consistent = rate([len({decision(r) for r in group}) == 1 for group in by_id.values()])
        seconds = sorted(r["seconds"] for r in rows)
        lines.append(f"| {rows[0]['model']} | " + " | ".join(cells) + f" | {consistent} | {seconds[len(seconds) // 2]} |")
        grading += [{"model": r["model"], "id": r["id"], "call": (r["ruling"] or {}).get("call", r["raw"]),
                     "explanation": (r["ruling"] or {}).get("explanation", ""), "correct": "", "useful": "", "clear": "", "safe": "", "notes": ""}
                    for r in rows if r["run"] == 1]
    table = "\n".join(lines)
    (RESULTS / f"{prompt}_{name}_summary.md").write_text(table + "\n", encoding="utf-8")
    if grading:
        with open(RESULTS / f"{prompt}_{name}_grading.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(grading[0]))
            writer.writeheader()
            writer.writerows(grading)
    print(table)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", help='labels like "Groq / openai/gpt-oss-120b"; default is every model that is set up')
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--summary", action="store_true", help="only rebuild the summary from saved results")
    args = parser.parse_args()
    load_dotenv()
    with open(SCENARIOS, newline="", encoding="utf-8") as f:
        scenarios = [s for s in csv.DictReader(f) if args.split in ("all", s["split"])]
    RESULTS.mkdir(exist_ok=True)
    if not args.summary:
        chunks = load_chunks()
        for label in args.models or available():
            run(label, scenarios, chunks, args.prompt, args.runs)
    summarize(args.prompt, args.split, {s["id"] for s in scenarios})


if __name__ == "__main__":
    main()
