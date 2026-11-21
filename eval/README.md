# Evaluation reconciliation and human grading

## Preserve the two datasets

`scenarios.csv` is Jason’s historical 18-dev/6-draft-test set. Existing v1/v2 saved answers and grading sheets use its d01–d18 IDs. Those scores are not scores on Timothy’s 40 cases.

`scenarios_timothy.csv` adapts the approved **30-development/10-final-test** set. It preserves the exact questions, answers, IDs, splits, full enforcement expectations and approval status from `evaluation/eval/`. Rebuild it with `uv run python eval/approved_cases.py`. The final ten remain fixed by `evaluation/eval/split_manifest.json`; no final-test model calls were made in this update.

The current app uses type=rule/play/out_of_scope. The source keys additionally distinguish clarify, refusal and insufficient evidence. The adapter retains expected_behavior and expected_enforcement for human grading. Generic type and spot labels are implementation mappings, not additional domain approvals. Automatic checks do not establish full ruling correctness or exact next-down math.

Matching Approved Ruling groups are excluded by ID for the adapted cases, keeping the underlying rules available. This is a leakage precaution, not proof that all paraphrased or cross-referenced examples are absent; inspect retrieved evidence.

## Run the current application on approved development inputs

```sh
uv run python eval/run_eval.py --scenarios eval/scenarios_timothy.csv --split dev --prompt v2 --models "Groq / openai/gpt-oss-120b"
```

Alternate scenario files write into a separate `eval/results/<scenario-file-stem>/` directory. The original scenarios and results remain unchanged. Do not run --split test until the application is ready and settings are frozen.

For a future judge run, pass the same source file:

```sh
uv run python eval/judge.py --scenarios eval/scenarios_timothy.csv eval/results/scenarios_timothy/v2_rag_groq-openai-gpt-oss-120b.jsonl
```

Judge output is written beside its input result file. This update makes no new model calls.

## Grade the actual saved v2 answers

Start with [the grouped answer review](grading/V2_REVIEW.md): **53 run-1 answers** across Groq, Gemma and Nemotron. Each includes the historical reference, actual output, proposed 1–3 scores for correct/useful/clear/safe, and the reason. Codex prepared these recommendations from saved answers and the pinned rulebook without reading the saved LLM-judge scores.

The editable [suggested review CSV](grading/v2_suggested_review.csv) separates suggested_* fields from final correct/useful/clear/safe/notes fields. Final human score fields remain blank. The original v1 and v2 human grading sheets are unchanged. Regeneration with `uv run python eval/prepare_grading_review.py` preserves human score fields already entered in the suggested review CSV. Do not promote suggestions to Timothy’s final grades without his approval.

Suggested starting cases:

1. **d08, momentum interception:** Groq wrongly gives a touchback at the 20; Gemma wrongly calls a safety; Nemotron correctly returns the ball to the interception spot at the 3.
2. **d09, forward fumble out of bounds:** Groq and Gemma wrongly place it at the 35; Nemotron correctly returns it to the 30.
3. **d03, DPI 30 yards downfield:** Groq chooses the wrong foul; Gemma mixes a spot foul with 15 yards; Nemotron gives DPI, 15 yards from previous spot, first down.
4. **d10:** distinguish illegal touching as a violation/receiving-team option from a foul, yardage penalty or immediate dead ball.
5. **d12/d13:** grade injection resistance and uncertainty separately from football facts.

Historical d13 is ambiguous: “secures it as he goes out” does not fix the instant of control precisely. Adjudicate that reference rather than treating every disagreement as a model error. Review targeting enforcement and general-quarterback exceptions against the 2026 source. Report human accuracy and human/judge agreement only after final grades are approved.
