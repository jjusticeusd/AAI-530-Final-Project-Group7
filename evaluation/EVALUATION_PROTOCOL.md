# Evaluation protocol and human rubric

Case status: all 40 questions, answers and notes approved by Timothy on November 16, 2026. The execution protocol remains proposed for team adoption. Results: not run.

## Five human criteria

Score each from 0 to 2; preserve individual criterion scores rather than only a total.

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Ruling correctness | Wrong ruling or unjustified definitive call | Partly correct, meaningful omission | Correct call or appropriate clarification/scope/abstention |
| Enforcement completeness | Wrong penalty, spot or down; fabricated facts | Correct core penalty, incomplete next situation | All applicable yards/spot/down correct, or correctly unresolved |
| Citation support | Fabricated, wrong edition or unsupported claim | Relevant citation with missing supporting detail | Traceable article/page supports each material rule claim |
| Usefulness and clarity | Confusing or unhelpful | Understandable with avoidable gaps | Plain explanation addressing the user's actual question |
| Responsible behavior | Invents facts, deceptive authority, wrong code | Some uncertainty/boundary handling, incomplete | Missing facts requested; scope and judgment boundaries respected |

Use N/A where a criterion truly does not apply (e.g., rule citations for a pure refusal to fabricate). Do not convert N/A to zero. For a clarification case, a precise invented yard line fails correctness and responsible behavior even if plausible. For scoring values or definitions, enforcement can be N/A. Human adjudication is required for equivalent wording and alternative valid citations.

A proposed per-answer pass requires 2 for ruling, 2 for enforcement if applicable, 2 for responsible behavior, 2 for citation support if a substantive rule claim is made, and at least 1 for clarity. This is an internal proposed threshold, not an instructor grade prediction. Report each criterion distribution and counts as well as pass rate.

## Execution

1. Timothy reviews all keys and references. Exclude unapproved cases from scored results; report excluded counts and IDs.
2. Freeze the split and record hashes of input/key files, source PDF, retrieval corpus, terminology, prompt files and code commit. Record whether Approved Rulings are indexed. Exclude all scenario/answer-key documentation from retrieval.
3. Use only the 30 dev cases to revise prompts. Save v1 and v2, the actual changed instructions, dev outputs, human scores and reasons for changes.
4. Fix model/provider versions, temperature, token limits, retrieval settings and context limits. Record local hardware, installed model digest and actual quantization; do not assume every Ollama model is 4-bit.
5. On the 10 test cases, run each model three times under the frozen final prompt. For paired comparisons provide the same retrieved passages to each model. Log truncation. Cache all raw outputs.
6. Compare the same model with retrieval disabled using the same questions and instructions where feasible. Label the no-retrieval condition explicitly. Corpus support checks are N/A there; still judge claims against the source for human citation accuracy.
7. Save failures and timeouts as outcomes. Report provider failures separately, completion coverage, and success among completed requests. Do not silently rerun only poor responses.
8. Score blind to model identity if feasible. Timothy records disagreements and final adjudications. Three repeats measure stability under these settings; they are not three independent questions.
9. Inspect final test failures only after prompt selection. A later revision requires a new test set or disclosure that the previous set became development data.

## Machine-readable result contract

One JSON object per generation in `eval/results/<run_id>.jsonl`:

`run_id`, `case_id`, `split`, `provider`, `model`, `model_digest`, `prompt_version`, `prompt_hash`, `condition` (rag/no_retrieval), `repeat` (1-3), `retrieved_chunk_ids`, `retrieved_context_hash`, `raw_output`, `parsed_output`, `parse_ok`, `citation_ids_present_in_context`, `latency_seconds`, `attempts`, `input_tokens`, `output_tokens`, `actual_cost_usd`, `error`, `human_scores`, `reviewer`, `review_date`.

Use null for unavailable cost/tokens and disclose availability. Distinguish measured cost from a rate-based estimate and from zero marginal API charge. Record timestamps and whether latency includes retries; use both first-attempt and end-to-end latency when possible.

Compare semantic call, actual penalty movement, spot and next down/distance; do not compare the whole response string. Separate valid citation IDs from supported citations, and retrieval recall from ruling correctness. Human reviewers may accept alternate citations only when they actually support the claim; document the reason rather than changing keys silently.

## Summary table to populate after runs

Model/condition | approved case count | completion coverage | ruling pass | enforcement pass | citation existence | citation support | responsible behavior | all-criteria pass | 3/3 semantic consistency | median/p95 latency | measured/estimated cost

For consistency, compare core call, behavior, penalty and enforcement across three runs, not surface phrasing. Also report consistently wrong answers separately. Stratify by category/behavior and show raw denominators. This sample is diagnostic, not a broad football accuracy estimate.

## Leakage and provenance

These scenarios are original AI-assisted variants, not verbatim Approved Rulings. The underlying rules must remain retrievable. If a test is later copied from an Approved Ruling, remove that exact answer/example from the evaluation index or label it direct answer retrieval. Do not place test answers in few-shot examples. Same-rule dev/test coverage is deliberate and limits claims about novel-rule generalization.

## AI-use record

Codex assisted with scenario drafting, source-text checks, rubric, terminology and packaging. The first draft incorrectly used a 15-yard OPI penalty; reading the pinned 2026 Rule 7-3-8-b corrected it to 10 yards. This is a documented rejected AI suggestion. Timothy approved the current keys on November 16, 2026. Human domain review is recorded; no meetings, model outputs or evaluation results are claimed.

## November 16 review update

Timothy approved all 40 current questions, answers and notes, including revised NCAA-040 (illegal forward pass beyond the neutral zone; third and 13 at A-27 after accepted enforcement). There are 30 approved development cases and 10 approved test cases. NCAA-035 was removed at his request. NCAA-037 and NCAA-041 use Approved Ruling principles explicitly and are development variants, not independent novel held-out scenarios. Domain approval does not represent model evaluation, team integration, or submission.

## Current split: November 16 update

The user authorized 30 development cases and 10 reserved final test cases. `eval/split_manifest.json` records IDs and hashes. All 10 final cases were selected from the previously unused test set; none came from the 17 previously run development cases. Saved v1/v2 outputs still describe their original smaller runs and are not a completed 30-case evaluation. Prompt development using the 30 cases is authorized; no model-weight training has occurred. Keep final-test answers out of retrieval and prompt examples.
