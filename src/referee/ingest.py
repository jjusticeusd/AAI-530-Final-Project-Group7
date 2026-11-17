import json
import re
import urllib.request
from pathlib import Path

from pypdf import PdfReader

URL = "https://ncaaorg.s3.amazonaws.com/championships/sports/football/rules/PRMFB_RulesBook.pdf"
DATA = Path(__file__).resolve().parents[2] / "data"
PDF = DATA / "rulebook.pdf"
CHUNKS = DATA / "chunks.jsonl"

PAGE_LABEL = re.compile(r"^F[ROI]-\d+\b|\bF[ROI]-\d+$", re.IGNORECASE)
RULE = re.compile(r"^RULE (\d+)$")
SECTION = re.compile(r"^SECTION (\d[\d ]*?) ?\.")
ARTICLE = re.compile(r"^ARTICLE (\d[\d ]*?) ?(?:\.|$)")
APPROVED = re.compile(r"^Approved Ruling (\d+-\d+-\d+)")
NEXT_TITLE = re.compile(r"\u2014ARTICLE \d+$")
CAPS_HEADING = re.compile(r"[A-Z0-9 ,;:.'()&/-]*[A-Z]{3}[A-Z0-9 ,;:.'()&/-]*")


def clean(text):
    # pypdf reads this PDF's periods as U+FFFD and splits kerned pairs like "T eam".
    text = text.replace("\ufffd", ".")
    return re.sub(r"\bT (?=[a-z])", "T", text)


def pages(path):
    return [clean(page.extract_text() or "") for page in PdfReader(path).pages]


def part_starts(texts):
    starts = {}
    for i, text in enumerate(texts):
        for line in text.splitlines():
            starts.setdefault(line.strip(), i)
    return starts["Part I:"], starts["Part II:"], starts["Part III:"]


def is_title(line):
    return len(line) < 80 and not line.rstrip().endswith((".", ":", ";", ",", ")"))


def split_rules(texts, first, last):
    chunks, current = [], None
    rule = section = None
    for page in range(first, last):
        for line in texts[page].splitlines():
            line = line.strip()
            if not line or PAGE_LABEL.search(line):
                continue
            if line == "Appendix A":
                return chunks
            if m := RULE.match(line):
                rule, section = m[1], None
                continue
            if m := SECTION.match(line):
                section = m[1].replace(" ", "")
                current = {"id": f"{rule}-{section}", "kind": "rule", "page": page + 1, "lines": [line]}
                chunks.append(current)
                continue
            if (m := ARTICLE.match(line)) and section:
                title = current["lines"].pop() if current and len(current["lines"]) > 1 and is_title(current["lines"][-1]) else None
                current = {"id": f"{rule}-{section}-{m[1].replace(' ', '')}", "kind": "rule", "page": page + 1, "lines": [title, line] if title else [line]}
                chunks.append(current)
                continue
            if current:
                current["lines"].append(line)
    return chunks


def split_approved(texts, first):
    chunks, current = [], None
    for page in range(first, len(texts)):
        for line in texts[page].splitlines():
            line = line.strip()
            if line.startswith("Term Page"):
                return chunks
            if not line or PAGE_LABEL.search(line) or NEXT_TITLE.search(line) or RULE.match(line) or SECTION.match(line) or CAPS_HEADING.fullmatch(line):
                continue
            if m := APPROVED.match(line):
                while current and len(current["lines"]) > 1 and not current["lines"][-1].endswith((".", ")", ":", "]")):
                    current["lines"].pop()
                current = {"id": f"A.R. {m[1]}", "kind": "approved_ruling", "page": page + 1, "lines": [line]}
                chunks.append(current)
                continue
            if current:
                current["lines"].append(line)
    return chunks


def main():
    if not PDF.exists():
        DATA.mkdir(exist_ok=True)
        urllib.request.urlretrieve(URL, PDF)
        print(f"Downloaded the rulebook to {PDF}")
    texts = pages(PDF)
    rules_start, standards_start, interpretations_start = part_starts(texts)
    chunks = split_rules(texts, rules_start, standards_start) + split_approved(texts, interpretations_start)
    chunks = [c for c in chunks if len(c["lines"]) > 1]
    with open(CHUNKS, "w", encoding="utf-8") as f:
        for chunk in chunks:
            lines = chunk.pop("lines")
            f.write(json.dumps({**chunk, "text": "\n".join(lines)}) + "\n")
    rules = sum(c["kind"] == "rule" for c in chunks)
    print(f"Wrote {rules} rule chunks and {len(chunks) - rules} approved-ruling chunks to {CHUNKS}")


if __name__ == "__main__":
    main()
