# Prompt and Testing Appendix

## Rule search testing

The rulebook is about 123k tokens, too big to send with every question. So the app searches the 473 rule sections (352 rules, 121 approved rulings) and sends only the top 6 to the model.

**Test set:** `eval/retrieval.csv` has 17 questions. Each one lists the rule that should come back. A question passes if that rule (or its approved ruling) is in the top 6. The test makes no model calls, so it is free and fast:

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

We kept version 3.

**Fixes found along the way:**
- "How many yards for pass interference" first ranked A.R. 9-2-3 at the top, because "how" and "many" are rare in the rulebook and scored high. A short stopword list put 7-3-8 first.
- "9-1-2" alone ranked 6th, because many sections cite it. Sections whose rule number is in the question now get a large boost.
- Typos like "tagerting" and "reciever" are mapped to the closest rulebook word. Rule numbers are never changed.
- Searching the last few chat turns let an earlier fair catch question push 3-1-3 out of an overtime search. Search now uses only the newest question.

**Why embeddings were dropped:** they lost questions that BM25 gets right: the rule-number lookup ("What does rule 9-1-2 say?"), false start, fair catch, onside kick, and fumble out of bounds. They also added about 750 MB to the install (PyTorch and its libraries), and the project should be light to set up on macOS and Windows.

**Still missed (BM25):**
- Laterals (7-2-1): the rule never says "lateral". It says the ball is passed backward.
- One forward pass per down (7-3-1): "forward pass" appears in 84 sections, so this one does not stand out.
- Quarter length (3-2-1) and players on the field (1-1-1).

Adding these to the slang list is the next fix to try.
