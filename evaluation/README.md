# Timothy's retrieval and evaluation prototype

Review branch contribution. This standalone prototype does not replace Jason's source package or claim final application readiness.

## What is here

- **40 approved scenarios:** 30 development, 10 reserved final tests. IDs and file hashes are in `eval/split_manifest.json`. Original questions/answers/notes were approved by Timothy on November 16, 2026.
- Rule-only BM25 retrieval with vocabulary expansion from the canonical `../referee/terminology.json`.
- v1/v2 prompt files, Groq connection/CLI scripts, bounded development runner, and citation/response validators.
- A completed **30-case v2 development run** using Groq `openai/gpt-oss-120b`; saved outputs and side-by-side review.
- Seven local tests for corpus isolation, retrieval and validation behavior.

## Actual development results

All 30 cases received API responses. Two rate-limit failure records were retained before successful resumption. Eleven responses passed the structural/excerpt checks; 19 had validation flags. **These counts are not football accuracy.** Generated outputs still contain substantive errors (including DPI enforcement, kickoff fair-catch placement and down/distance calculations). Timothy has approved the reference answers, not these generated answers. Human grading is pending. Do not run the final ten until the implementation is ready and settings are frozen.

See [generated versus approved answers](DEV_RUN_V2_REVIEW.md) and [summary](eval/results/dev30_v2_summary.json). V2 used development-only demonstrations; no model weights were trained. Some newly moved development cases were previously in the larger draft test split; the ten final cases were never taken from model-exposed development cases.

## Set up and run

From the repository root, use the existing uv-managed project (Python 3.13+):

```sh
uv sync --locked
uv run python evaluation/scripts/prepare_reference.py
```

The official PDF URL is mutable. Preparation downloads it locally and verifies `source_manifest.json` before parsing. If the source now differs, stop for edition review. If you already have the pinned PDF, use `--pdf /absolute/path/to/rulebook.pdf`. No PDF or derived corpus is committed.

Create `evaluation/.env` privately with `GROQ_API_KEY=your_key`. Alternatively supply GROQ_API_KEY through your environment. The scripts read that file explicitly; they do not print it.

```sh
uv run python evaluation/scripts/check_groq.py
uv run python evaluation/scripts/referee_pipeline_v2.py --question 'A backward pass hits the ground inbounds. Is it dead?' --retrieve-only
uv run python evaluation/scripts/referee_pipeline_v2.py --question 'A backward pass hits the ground inbounds. Is it dead?' --model openai/gpt-oss-120b
uv run python evaluation/scripts/referee_pipeline_v2.py --dev --model openai/gpt-oss-120b --output evaluation/eval/results/new_dev_run.jsonl
uv run python evaluation/scripts/build_dev_report.py
uv run python -m unittest discover -s evaluation/tests
```

Groq calls consume the account's quota. The default model without --model is gpt-oss-20b; the supplied v2 results used gpt-oss-120b. Each batch command sends development questions only. The runner records bad responses rather than silently retrying them for a better answer. It stops on rate limits; the optional `run_dev_batch.py` resumes the fixed 30-case run with bounded waits. It is intended for reproducing that run, not for selectively replacing failed rulings.

The report builder currently reads the supplied `groq_dev30_v2_120b.jsonl`; adapt its source path deliberately to review a new run. Preserve old results and hashes. The GitHub export omits full retrieved rule text; IDs, context hashes, raw model output and validation outcomes remain. The original full-context logs remain local. `pipeline_hash` refers to the original run script; this contribution adjusts the vocabulary path to use the canonical source file, so reproducing it creates a distinct run.

## Scope and remaining work

Only the development inputs enter generation. Answer keys are used by the separate report/scoring step. The reserved tests are committed for review and future scoring but must not enter retrieval, few-shot examples or prompt tuning. Rule-only retrieval excludes Approved Rulings; the toe/heel interpretation case exposes a limitation of that corpus choice.

JSON-object mode does not enforce the declared field types. Existing validators flag strings where citation objects or integers were required; exact excerpt checks also flag altered punctuation or ellipses. A citation that exists is not necessarily supported. Next work: explicit structured-output schema, improved article retrieval, enforcement checking, human grading, and a shared integration interface before UI work. No final-test run, hosted/local comparison or final-submission claim is included here.

## Current application integration

Jason’s current implementation is in `referee/`. For future model evaluation, use `eval/scenarios_timothy.csv` with the current runner as documented in `../eval/README.md`. This folder preserves the approved source keys and historical prototype; it is not the active application implementation.
