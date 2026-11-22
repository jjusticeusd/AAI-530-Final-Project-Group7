import json
import re
from pathlib import Path

from referee.retrieve import retrieve

PROMPTS = Path(__file__).parent / "prompts"
PROMPT = "v2"
MAX_TURNS = 2
CONTEXTS = ["rag", "full"]
RULE_NUMBER = re.compile(r"\d+-\d+(?:-\d+)?")
MENTIONED = re.compile(r"\b\d+-\d+-\d+\b|(?<=Rule )\d+-\d+\b")
REFERENCE = re.compile(r"\s*\((?:A\.R\.|Rules?) [^)]*\)")
PENALTY_LINE = re.compile(r"PENALTY\s*(?:\[[^\]]*\])?\s*[—-]")


def system_prompt(version=PROMPT):
    return (PROMPTS / f"{version}.md").read_text(encoding="utf-8")


def context_chunks(chunks, question, context="rag", exclude=()):
    pool = [c for c in chunks if c["id"] not in exclude]
    if context == "full":
        return pool
    return with_penalties(retrieve(pool, question), pool)


def penalties(chunk, pool, skip):
    if not re.fullmatch(r"\d+-\d+-\d+", chunk["id"]) or PENALTY_LINE.search(
        chunk["text"]
    ):
        return []
    section, article = chunk["id"].rsplit("-", 1)
    sources = [
        c
        for c in pool
        if c["id"].startswith(f"{section}-")
        and re.search(rf"PENALTY\W*\[[^\]]*\bARTICLE {article}\b", c["text"])
    ]
    sources += [c for c in pool if c["id"] == section]
    return [
        (c["id"], c["text"][m.start() :])
        for c in sources
        if c["id"] not in skip and (m := PENALTY_LINE.search(c["text"]))
    ]


def with_penalties(found, pool):
    ids = {c["id"] for c in found}
    out = []
    for c in found:
        if extra := penalties(c, pool, ids):
            c = {
                **c,
                "text": c["text"]
                + "".join(f"\n\nPenalty (from {i}): {t}" for i, t in extra),
                "penalty_from": [i for i, _ in extra],
            }
            ids.update(c["penalty_from"])
        out.append(c)
    return out


def messages(chunks, history, version=PROMPT, exclude=(), context="rag"):
    recent = history[-(MAX_TURNS * 2 + 1) :]
    question = next(m["content"] for m in reversed(recent) if m["role"] == "user")
    found = context_chunks(chunks, question, context, exclude)
    rules = "\n\n".join(f"[p. {c['page']}] {c['id']}\n{c['text']}" for c in found)
    return [
        {"role": "system", "content": system_prompt(version).replace("{rules}", rules)},
        *recent,
    ], found


def parse(text):
    start, end = text.find("{"), text.rfind("}")
    try:
        ruling = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return ruling if isinstance(ruling, dict) else None


def squash(text):
    text = re.sub("[\u2010\u2011]", "-", REFERENCE.sub("", text)).lower()
    text = re.sub(r"\(\w{1,3}\)", " ", text)
    return " ".join(re.sub(r"[^\w\s-]", " ", text).split())


def quoted(quote, text):
    text = f" {text} "
    at = 0
    for part in filter(None, map(squash, re.split(r"\.\.\.|\u2026", quote))):
        part = f" {part} "
        at = text.find(part, at)
        if at < 0:
            return False
        at += len(part) - 1
    return True


def verify(ruling, found):
    retrieved = {c["id"].split()[-1] for c in found}
    attached = {i for c in found for i in c.get("penalty_from", [])}

    def covered(n):
        return n in attached or any(n == i or n.startswith(f"{i}-") for i in retrieved)

    cited = [r for r in ruling.get("rules") or [] if isinstance(r, str)]
    unverified = [
        r for r in cited if not any(covered(n) for n in RULE_NUMBER.findall(r))
    ]
    prose = " ".join(str(ruling.get(k) or "") for k in ("call", "explanation"))
    unverified += [
        n
        for n in dict.fromkeys(MENTIONED.findall(prose))
        if not covered(n) and not any(n in r for r in unverified)
    ]
    quote = ruling.get("quote") or ""
    quote_found = not quote or quoted(quote, squash(" ".join(c["text"] for c in found)))
    return unverified, quote_found


def rule(chunks, send, history, version=PROMPT, exclude=(), context="rag"):
    prompt, found = messages(chunks, history, version, exclude, context)
    raw = send(prompt)
    result = {"raw": raw, "retrieved": [c["id"] for c in found], "found": found}
    ruling = parse(raw) if raw is not None else None
    if ruling is None:
        return {
            **result,
            "ruling": None,
            "unverified": [],
            "quote_found": False,
            "needs_review": True,
        }
    unverified, quote_found = verify(ruling, found)
    needs_review = (
        bool(ruling.get("needs_review")) or bool(unverified) or not quote_found
    )
    return {
        **result,
        "ruling": ruling,
        "unverified": unverified,
        "quote_found": quote_found,
        "needs_review": needs_review,
    }
