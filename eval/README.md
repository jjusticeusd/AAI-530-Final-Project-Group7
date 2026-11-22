# Evaluation

## Scenario sets

- `scenarios.csv`: the first set. 18 dev questions (d01-d18) and 6 safety questions (t01-t06).
- `scenarios_approved.csv`: the 40 approved questions, 30 dev and 10 final test (IDs NCAA-001 to NCAA-041). Matching Approved Rulings are listed in `exclude` so the answer is not retrieved word for word; the underlying rules stay searchable. `penalty_yards` is blank on no-foul plays and on NCAA-017 (a DPI spot foul walked off 8 yards), because the app reports the yards on the rule's PENALTY line, or null when there is no foul.
- `retrieval.csv`: 19 rule-search questions for `retrieval_eval.py` (no model calls).

## Results

| Folder | Set | Prompt | Models | Judge |
|---|---|---|---|---|
| `results/` | first set, dev | v1, v2 | gpt-oss (Groq), gemma, Nemotron | Groq qwen3.8-27b |
| `results/` (`v1_full_*`) | first set, dev, whole rulebook instead of search | v1 | Nemotron | - |
| `results/scenarios_approved/` | approved, dev and test | v2 | gpt-oss (OpenRouter, Groq host), gemma, Nemotron | OpenRouter qwen3.8-27b |
| `results/safety/` | first set, safety (t01-t06) | v2 | gpt-oss (OpenRouter, Groq host), gemma, Nemotron | OpenRouter qwen3.8-27b |
| `results/dropped/` | first set, dev | v1 | gpt-oss-20b, a smaller model we tried and dropped | - |

Each folder has one `<prompt>_<context>_<model>.jsonl` file per model (3 runs per question), a `judge_*.jsonl` file per model next to it, and a `*_summary.md` table rebuilt by `--summary`.

## Run

```sh
uv run python eval/run_eval.py --scenarios eval/scenarios_approved.csv --split dev --prompt v2
uv run python eval/run_eval.py --scenarios eval/scenarios_approved.csv --split dev --prompt v2 --summary
uv run python eval/judge.py --scenarios eval/scenarios_approved.csv eval/results/scenarios_approved/v2_rag_*.jsonl
```

A scenario file other than `scenarios.csv` writes to `results/<file name>/`, so earlier results are not overwritten. The safety set is `--scenarios eval/scenarios.csv --split test --results-dir eval/results/safety`. Judge output is written next to the results file it scores, and a rerun skips answers already judged. Do not run `--split test` until the prompt and settings are final.

## Human grading

Grade in `results/scenarios_approved/v2_rag_dev_grading.csv` and `v2_rag_test_grading.csv`: fill in `correct`, `useful`, `clear`, and `safe` (1-3, see `rubric.md`) and `notes` for each answer. `--summary` keeps entered grades when it rewrites the sheets. Then compare with the judge:

```sh
uv run python eval/judge.py eval/results/scenarios_approved/v2_rag_*.jsonl --compare eval/results/scenarios_approved/v2_rag_dev_grading.csv eval/results/scenarios_approved/v2_rag_test_grading.csv
```

`grading/` holds an earlier review of the first set's v2 answers with AI-suggested scores. It is not the grading sheet.
