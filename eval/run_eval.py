import argparse
import csv
import json
import re
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from referee import backends
from referee.backends import ask, available, backend
from referee.retrieve import load_chunks
from referee.ruling import (
    CONTEXTS,
    PROMPT,
    RULE_NUMBER,
    context_chunks,
    quoted,
    rule,
    squash,
    with_penalties,
)

EVAL = Path(__file__).parent
SCENARIOS = EVAL / "scenarios.csv"
RESULTS = EVAL / "results"
LONG_CONTEXT_OLLAMA_NUM_CTX = 98304
CHECKS = [
    "parsed",
    "type",
    "foul",
    "yards",
    "spot",
    "rule",
    "citations",
    "quote",
    "review",
]
GRADES = ["correct", "useful", "clear", "safe", "notes"]
MODELS = [
    "Groq / openai/gpt-oss-120b",
    "OpenRouter / nvidia/nemotron-3-ultra-550b-a55b:free",
    "Ollama / gemma3:12b",
]


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
        checks["spot"] = (
            s["enforcement_spot"] in (r.get("enforcement_spot") or "").lower()
        )
    if s["rules"]:
        cited = numbers(x for x in r.get("rules") or [] if isinstance(x, str))
        checks["rule"] = any(
            c == w or c.startswith(f"{w}-")
            for c in cited
            for w in numbers(split(s["rules"]))
        )
    if s["needs_review"]:
        checks["review"] = result["needs_review"] == (s["needs_review"] == "true")
    return checks


def decision(result):
    r = result["ruling"] or {}
    return json.dumps(
        [
            r.get("type"),
            r.get("foul"),
            r.get("penalty_yards"),
            (r.get("enforcement_spot") or "").lower(),
        ]
    )


def quote_found(r, s, chunks):
    quote = (r["ruling"] or {}).get("quote")
    if not quote:
        return r["quote_found"]
    pool = [c for c in chunks if c["id"] not in set(split(s["exclude"]))]
    if r.get("context", "rag") == "rag":
        by_id = {c["id"]: c for c in pool}
        found = with_penalties([by_id[i] for i in r["retrieved"] if i in by_id], pool)
    else:
        found = context_chunks(pool, s["question"], r.get("context", "rag"))
    return quoted(quote, squash(" ".join(c["text"] for c in found)))


def load(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def run(label, scenarios, chunks, prompt, runs, context):
    path = RESULTS / f"{prompt}_{context}_{slug(label)}.jsonl"
    done = {(r["id"], r["run"]) for r in load(path)}
    send = backend(label)
    with open(path, "a", encoding="utf-8") as f:
        for s in scenarios:
            for n in range(1, runs + 1):
                if (s["id"], n) in done:
                    continue
                start = time.perf_counter()
                result = rule(
                    chunks,
                    lambda m: ask(send, m),
                    [{"role": "user", "content": s["question"]}],
                    prompt,
                    set(split(s["exclude"])),
                    context,
                )
                seconds = round(time.perf_counter() - start, 2)
                if result["raw"] is None:
                    print(
                        f"  {label}: no answer for {s['id']} run {n}, stopping. Rerun later to continue."
                    )
                    return
                row = {
                    "id": s["id"],
                    "run": n,
                    "model": label,
                    "prompt": prompt,
                    "context": context,
                    "seconds": seconds,
                    "retrieved": result["retrieved"] if context == "rag" else [],
                    "raw": result["raw"],
                    "ruling": result["ruling"],
                    "unverified": result["unverified"],
                    "quote_found": result["quote_found"],
                    "needs_review": result["needs_review"],
                    "checks": score(s, result),
                }
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(
                    f"  {label} {s['id']} run {n}: {seconds}s {'ok' if all(row['checks'].values()) else 'miss'}"
                )


def rate(values):
    return f"{sum(values)}/{len(values)}" if values else "-"


def summarize(prompt, context, name, scenarios):
    lines = [
        "| Model | " + " | ".join(CHECKS) + " | consistent | median s |",
        "|" + "---|" * (len(CHECKS) + 3),
    ]
    grading = []
    chunks = load_chunks()
    for path in sorted(RESULTS.glob(f"{prompt}_{context}_*.jsonl")):
        rows = [r for r in load(path) if r["id"] in scenarios]
        if not rows:
            continue
        for r in rows:
            r["quote_found"] = quote_found(r, scenarios[r["id"]], chunks)
            r["checks"] = score(scenarios[r["id"]], r)
        by_id = defaultdict(list)
        for r in rows:
            by_id[r["id"]].append(r)
        cells = [
            rate([r["checks"][c] for r in rows if c in r["checks"]]) for c in CHECKS
        ]
        consistent = rate(
            [
                len({decision(r) for r in group}) == 1
                for group in by_id.values()
                if len(group) > 1
            ]
        )
        seconds = sorted(r["seconds"] for r in rows)
        lines.append(
            f"| {rows[0]['model']} | "
            + " | ".join(cells)
            + f" | {consistent} | {seconds[len(seconds) // 2]} |"
        )
        grading += [
            {
                "model": r["model"],
                "id": r["id"],
                "question": scenarios[r["id"]]["question"],
                "expected": scenarios[r["id"]]["answer"],
                "call": (r["ruling"] or {}).get("call", r["raw"]),
                "explanation": (r["ruling"] or {}).get("explanation", ""),
                **dict.fromkeys(GRADES, ""),
            }
            for r in rows
            if r["run"] == 1
        ]
    table = "\n".join(lines)
    (RESULTS / f"{prompt}_{context}_{name}_summary.md").write_text(
        table + "\n", encoding="utf-8"
    )
    sheet = RESULTS / f"{prompt}_{context}_{name}_grading.csv"
    if sheet.exists():
        with open(sheet, newline="", encoding="utf-8") as f:
            graded = {(g["model"], g["id"]): g for g in csv.DictReader(f)}
        for g in grading:
            old = graded.get((g["model"], g["id"]), {})
            g.update({k: old.get(k, "") for k in GRADES})
    if grading:
        with open(sheet, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(grading[0]))
            writer.writeheader()
            writer.writerows(grading)
    print(table)


def main():
    global RESULTS
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=SCENARIOS,
        help="Scenario CSV; defaults preserve legacy runs",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        help="Separate output directory for an alternate scenario set",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        help='labels like "Groq / openai/gpt-oss-120b"; default is the MODELS list, skipping any that are not set up',
    )
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument(
        "--context",
        default="rag",
        choices=CONTEXTS,
        help="rag: top search hits; full: every chunk; rules: every rule section, no approved rulings",
    )
    parser.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--summary",
        action="store_true",
        help="only rebuild the summary from saved results",
    )
    args = parser.parse_args()
    if args.results_dir:
        RESULTS = args.results_dir
    elif args.scenarios.resolve() != SCENARIOS.resolve():
        RESULTS = RESULTS / args.scenarios.stem
    load_dotenv()
    with open(args.scenarios, newline="", encoding="utf-8") as f:
        scenarios = [s for s in csv.DictReader(f) if args.split in ("all", s["split"])]
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.context != "rag":
        backends.OLLAMA_NUM_CTX = LONG_CONTEXT_OLLAMA_NUM_CTX
    if not args.summary:
        chunks = load_chunks()
        for label in args.models or [m for m in MODELS if m in available()]:
            run(label, scenarios, chunks, args.prompt, args.runs, args.context)
    summarize(args.prompt, args.context, args.split, {s["id"]: s for s in scenarios})


if __name__ == "__main__":
    main()
