# Evaluation

## Scenario sets

- `scenarios.csv`: the first 18 dev and 6 draft test questions (IDs d01-d18, t01-t06). The saved v1 and v2 results and grading sheets in `results/` use these IDs.
- `scenarios_timothy.csv`: the 40 approved questions, 30 dev and 10 final test (IDs NCAA-001 to NCAA-041). Matching Approved Rulings are listed in `exclude` so the answer is not retrieved word for word; the underlying rules stay searchable.

## Run

```sh
uv run python eval/run_eval.py --scenarios eval/scenarios_timothy.csv --split dev --prompt v2 --models "Groq / openai/gpt-oss-120b"
uv run python eval/judge.py --scenarios eval/scenarios_timothy.csv eval/results/scenarios_timothy/v2_rag_groq-openai-gpt-oss-120b.jsonl
```

A scenario file other than `scenarios.csv` writes to `results/<file name>/`, so earlier results are not overwritten. Judge output is written next to the results file it scores. Do not run `--split test` until the prompt and settings are final.

## Grading the saved v2 answers

`grading/V2_REVIEW.md` groups the 53 run-1 v2 answers by question, with the reference answer, the model output, and suggested 1-3 scores for correct, useful, clear and safe. `grading/v2_suggested_review.csv` has the same suggestions in `suggested_*` columns and blank `correct`, `useful`, `clear`, `safe` and `notes` columns for the final human grades. Suggestions are not grades until a human reviewer confirms them.
