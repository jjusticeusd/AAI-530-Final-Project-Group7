import json
import math
import re
from collections import Counter
from difflib import get_close_matches

from referee.ingest import CHUNKS

TOP_K = 6
SYNONYMS = {
    "lateral": "backward pass",
    "onside": "free kick restraining line",
    "overtime": "extra period",
    "ot": "extra period",
    "quarter": "period",
    "pi": "pass interference",
    "dpi": "defensive pass interference",
    "opi": "offensive pass interference",
    "extra point": "try",
    "pat": "try",
    "conversion": "try",
    "pick six": "intercept touchdown",
    "two minute warning": "two-minute timeout",
    "quarterback": "passer",
    "qb": "passer",
    "allowed": "legal",
}
STOPWORDS = set("a allow allowed an and are can do does for how i if in is it many much of on one or play say says the to what when where which who why with".split())


def load_chunks():
    return [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines()]


def stem(word):
    for suffix in ("ing", "ed", "es", "s", "e"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix) and not word.endswith("ss"):
            return word[: -len(suffix)]
    return word


def words(text):
    return [stem(w) for w in re.findall(r"\d+-\d+(?:-\d+)?|[a-z]+", text.lower()) if w not in STOPWORDS]


def expand(question):
    lowered = question.lower()
    return " ".join([question, *(v for k, v in SYNONYMS.items() if re.search(rf"\b{k}s?\b", lowered))])


def correct(word, vocab):
    if word in vocab or word[0].isdigit():
        return word
    return next(iter(get_close_matches(word, vocab, n=1, cutoff=0.8)), word)


def keyword_scores(chunks, question):
    docs = [Counter(words(f"{c['id']} {c['text']}")) for c in chunks]
    df = Counter(w for d in docs for w in d)
    avg = sum(d.total() for d in docs) / len(docs)
    asked = {correct(w, df) for w in words(expand(question))}

    def bm25(d, k1=1.2, b=0.75):
        norm = k1 * (1 - b + b * d.total() / avg)
        return sum(math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5)) * d[w] * (k1 + 1) / (d[w] + norm) for w in asked if w in d)

    return [bm25(d) + 100 * (c["id"].split()[-1] in asked) for c, d in zip(chunks, docs)]


def retrieve(chunks, question):
    scores = keyword_scores(chunks, question)
    top = sorted(range(len(chunks)), key=scores.__getitem__, reverse=True)[:TOP_K]
    return [chunks[i] for i in top]
