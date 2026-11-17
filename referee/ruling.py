import json
import re
from pathlib import Path

from referee.retrieve import retrieve

PROMPTS = Path(__file__).parent / "prompts"
PROMPT = "v2"
MAX_TURNS = 2
CONTEXTS = ["rag", "full", "rules"]
RULE_NUMBER = re.compile(r"\d+-\d+(?:-\d+)?")
MENTIONED = re.compile(r"\b\d+-\d+-\d+\b|(?<=Rule )\d+-\d+\b")


def system_prompt(version=PROMPT):
    return (PROMPTS / f"{version}.md").read_text(encoding="utf-8")


def context_chunks(chunks, question, context="rag", exclude=()):
    pool = [c for c in chunks if c["id"] not in exclude]
    if context == "full":
        return pool
    if context == "rules":
        return [c for c in pool if not c["id"].startswith("A.R.")]
    return retrieve(pool, question)


def messages(chunks, history, version=PROMPT, exclude=(), context="rag"):
    recent = history[-(MAX_TURNS * 2 + 1):]
    question = next(m["content"] for m in reversed(recent) if m["role"] == "user")
    found = context_chunks(chunks, question, context, exclude)
    rules = "\n\n".join(f"[p. {c['page']}] {c['id']}\n{c['text']}" for c in found)
    return [{"role": "system", "content": system_prompt(version).replace("{rules}", rules)}, *recent], found


def parse(text):
    start, end = text.find("{"), text.rfind("}")
    try:
        ruling = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return ruling if isinstance(ruling, dict) else None


def squash(text):
    return " ".join(re.sub("[\u2018\u2019]", "'", re.sub("[\u201c\u201d]", '"', text)).lower().split())


def verify(ruling, found):
    retrieved = {c["id"].split()[-1] for c in found}
    covered = lambda n: any(n == i or n.startswith(f"{i}-") for i in retrieved)
    cited = [r for r in ruling.get("rules") or [] if isinstance(r, str)]
    unverified = [r for r in cited if not any(covered(n) for n in RULE_NUMBER.findall(r))]
    prose = " ".join(str(ruling.get(k) or "") for k in ("call", "explanation"))
    unverified += [n for n in dict.fromkeys(MENTIONED.findall(prose)) if not covered(n) and not any(n in r for r in unverified)]
    quote = ruling.get("quote") or ""
    quote_found = not quote or squash(quote) in squash(" ".join(c["text"] for c in found))
    return unverified, quote_found


def rule(chunks, send, history, version=PROMPT, exclude=(), context="rag"):
    prompt, found = messages(chunks, history, version, exclude, context)
    raw = send(prompt)
    result = {"raw": raw, "retrieved": [c["id"] for c in found], "found": found}
    ruling = parse(raw) if raw is not None else None
    if ruling is None:
        return {**result, "ruling": None, "unverified": [], "quote_found": False, "needs_review": True}
    unverified, quote_found = verify(ruling, found)
    needs_review = bool(ruling.get("needs_review")) or bool(unverified) or not quote_found
    return {**result, "ruling": ruling, "unverified": unverified, "quote_found": quote_found, "needs_review": needs_review}
