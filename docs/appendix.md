# Prompt and Testing Appendix

## Rule search testing

The rulebook is about 123k tokens, too big to send with every question. So the app searches the 473 rule sections (352 rules, 121 approved rulings) and sends only the top 6 to the model.

**Test set:** `eval/retrieval.csv` has 19 questions (17 at first, plus two from app testing). Each one lists the rule that should come back. A question passes if that rule (or its approved ruling) is in the top 6. The test makes no model calls, so it is free and fast:

```
uv run python eval/retrieval_eval.py
```

**Results:**

| Version | Score | What changed |
|---|---|---|
| 1. Rare-word overlap | 9/17 | Scores a section by how many rare question words it shares. |
| 2. + newest question only, stemming, slang list | 9/17 | Search uses only the latest message, "passes" matches "pass", and slang like "onside" and "PI" adds the rulebook's words. Fixed real bugs but did not move the score. |
| 3. + BM25 ranking | **13/17** | Credits a word more when it appears several times, and stops long sections from winning just for being long. Found onside kicks, punt formation, fair catch, and fumbles out of bounds. |
| 4. + title boost | 10-11/17 | Extra weight for words in a rule's title. Worse, so dropped. |
| 5. Embeddings only | 11/17 | `all-MiniLM-L6-v2` from sentence-transformers. |
| 6. Embeddings + BM25 (hybrid) | 11/17 | Both rankings merged with reciprocal rank fusion. Worse, so dropped. |
| 7. BM25 + more slang and filler words | 15/19 (13/17 on the first 17) | "quarterback" and "qb" add "passer", "allowed" adds "legal", and "allow", "allowed", "one", and "play" are ignored. Kept. |
| 8. + team slang list (`referee/terminology.json`) | 15/19 | 77 phrases from Timothy, like "horse collar" and "DPI". "punt" and "fair catch" were removed: they added "scrimmage kick" and "valid signal", which pushed A.R. 6-5-5 out of the top 6 (14/19). Same score, wider slang coverage. Kept. |

We kept version 3, then added versions 7 and 8 on top.

**Fixes found along the way:**
- "How many yards for pass interference" first ranked A.R. 9-2-3 at the top, because "how" and "many" are rare in the rulebook and scored high. A short stopword list put 7-3-8 first.
- "9-1-2" alone ranked 6th, because many sections cite it. Sections whose rule number is in the question now get a large boost.
- Typos like "tagerting" and "reciever" are mapped to the closest rulebook word. Rule numbers are never changed.
- Searching the last few chat turns let an earlier fair catch question push 3-1-3 out of an overtime search. Search now uses only the newest question.

**Why embeddings were dropped:** they lost questions that BM25 gets right: the rule-number lookup ("What does rule 9-1-2 say?"), false start, fair catch, onside kick, and fumble out of bounds. They also added about 750 MB to the install (PyTorch and its libraries), and the project should be light to set up on macOS and Windows.

**Version 7 fixes, found by testing the app:**
- "Can I tackle the quarterback" found only approved rulings, all about hits after the throw, so every model called roughing the passer. The rulebook says "passer", not "quarterback". Version 7 adds rule 9-1-9 itself.
- "How many forward passes are allowed on one play" ranked goal lines (1-1-2) first, because "allowed" is rare in the rulebook. In version 7, all six results are pass rules.

**What the score does not show:** a question passes if the approved ruling comes back, even when the rule itself does not. So the two version 7 fixes above did not change the score: A.R. 9-1-9 and 7-3-1 were already in the top 6.

**Still missed (BM25):**
- Laterals (7-2-1): the rule never says "lateral". It says the ball is passed backward.
- One forward pass per down (7-3-1): "how many forward passes in a single play" and "can you throw the ball forward two times in one play?" still miss it. "Forward pass" appears in 84 sections, so this one does not stand out.
- Quarter length (3-2-1) and players on the field (1-1-1).

Adding these to the slang list is the next fix to try.
