import csv
from pathlib import Path

from referee.retrieve import load_chunks, retrieve

TESTS = Path(__file__).parent / "retrieval.csv"


def main():
    chunks = load_chunks()
    with open(TESTS, newline="", encoding="utf-8") as f:
        tests = list(csv.DictReader(f))
    hits = 0
    for t in tests:
        got = [c["id"] for c in retrieve(chunks, t["question"])]
        ok = any(g.split()[-1] == t["rule"] for g in got)
        hits += ok
        print("OK  " if ok else "MISS", t["rule"].ljust(7), t["question"][:60], "->", got)
    print(f"{hits}/{len(tests)} found the right rule in the top {len(got)}")


if __name__ == "__main__":
    main()
