# NCAA Football Referee

AAI-530 Final Project, Group 7: Jason Justice and Timothy Hays.

Ask an NCAA football rules question or describe a play, and get a ruling that cites rule numbers from the official 2026 NCAA Football Rules and Interpretations. The app searches the rulebook, asks a model for a structured ruling (call, yards, enforcement spot, rules, quote), then checks in code that every cited rule and the quote came from the rulebook text the model was given.

A study aid for fans, players, and officials. Not for live games.

![The app ruling on a described play: offensive pass interference, 10 yards from the previous spot, with the rules it cited](docs/images/pass_interference.png)

## Results at a glance

The 10 held-out test questions, written and approved by our football player, 3 runs per model:

| Model | Runs on | Expected rule cited | Spot right | Citations found in the retrieved text | Same ruling all 3 runs | Judge: correct (1-3) | Median seconds |
|---|---|---|---|---|---|---|---|
| Nemotron | OpenRouter, free tier | 20/26 | 6/6 | 28/29 | 9/10 | 2.40 | 14.0 |
| gpt-oss-120b | OpenRouter, Groq host | 17/27 | 5/6 | 30/30 | 7/10 | 2.00 | 1.1 |
| gemma3:12b | Ollama, local | 18/27 | 3/6 | 27/30 | 10/10 | 2.30 | 8.1 |

Section 7 of the [report](docs/report.md) has every result, including the safety tests and how the prompt changed.

## Reviewing without running it

- [`docs/report.md`](docs/report.md): what we built, how it works, results, limitations, ethics, and how we used AI.
- [`docs/appendix.md`](docs/appendix.md): every prompt version, the test cases, the evaluation criteria, and selected outputs.
- [`docs/presentation.md`](docs/presentation.md): presentation outline and demo script.
- [`eval/results/`](eval/results/): every saved model answer and the summary tables ([map of the folders](eval/README.md#results)).
- [`docs/images/`](docs/images/): app screenshots.

## Setup

Works on macOS and Windows.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Get at least one model backend:
   - A free OpenRouter API key: https://openrouter.ai/keys (Nemotron, the default model), or
   - A free Groq API key: https://console.groq.com/keys (gpt-oss-120b), or
   - [Ollama](https://ollama.com) running locally with `ollama pull gemma3:12b` (no key needed, about 8 GB).
3. Copy `.env.example` to `.env` and add your key(s). Never commit `.env`.
4. Download the rulebook into `data/` and split it by rule number:
   ```
   uv run python -m referee.ingest
   ```
5. Start the app:
   ```
   uv run streamlit run referee/app.py
   ```

The sidebar lists only the models you have set up.

## Evaluate

Rule search only (no model calls, free):
```
uv run python eval/retrieval_eval.py
```

Rulings from the models. Each question runs 3 times per model. Answers are saved as they come in, so a stopped run picks up where it left off. `--summary` rebuilds the tables from saved answers with no model calls:
```
uv run python eval/run_eval.py --scenarios eval/scenarios_approved.csv --split dev
uv run python eval/run_eval.py --scenarios eval/scenarios_approved.csv --split dev --summary
```

By default the eval runs gpt-oss-120b and Nemotron on OpenRouter and gemma on Ollama, skipping any that are not set up. [`eval/README.md`](eval/README.md) has the LLM judge, the safety set, and human grading.

## Tests and lint

```
uv run pytest
uv run python lint.py
```

The tests cover the citation and quote checks. `lint.py` runs ruff's basic checks, fixes what it can, and formats the code.

## Layout

| Path | What it is |
|---|---|
| `referee/ingest.py` | Downloads the official PDF (not stored in this repo) and splits it into rule chunks (like `9-1-2`) and approved-ruling chunks (like `A.R. 9-1-2`) |
| `referee/retrieve.py` | Keyword search (BM25) over the chunks, with a rule-number boost, typo fixes, and a football slang list |
| `referee/ruling.py` | Builds the prompt, attaches penalties written elsewhere in a section, parses the JSON ruling, and checks the citations and the quote |
| `referee/backends.py` | Groq, OpenRouter, and Ollama clients with retries |
| `referee/app.py` | The Streamlit chat app |
| `referee/prompts/` | System prompt versions v0, v1, v2 (v2 is current) |
| `referee/terminology.json` | Football slang mapped to rulebook wording, used by search |
| `eval/scenarios.csv` | First set: 18 dev questions and 6 safety questions |
| `eval/scenarios_approved.csv` | 40 approved questions: 30 dev, 10 test |
| `eval/retrieval.csv`, `eval/retrieval_eval.py` | 19 rule-search questions and their scorer |
| `eval/run_eval.py` | Runs the questions on each model and scores them; writes summary tables and grading sheets |
| `eval/judge.py`, `eval/judge_prompt.md`, `eval/rubric.md` | LLM judge, its prompt, and the 1-3 rubric shared with human grading |
| `eval/results/` | Saved answers, judge scores, summaries, and grading sheets |
| `tests/` | Unit tests for the checks |
| `docs/` | Report, appendix, presentation, slang guide, screenshots, and `planning/` (assignment spec, plan, schedule) |
| `lint.py` | Lint and format |

## Football terminology

See [slang to rulebook wording](docs/slang_to_rulebook.md) for common player, coach and broadcaster phrases. The matching [JSON vocabulary](referee/terminology.json) is used by rule search. Special-teams descriptions use kicking team and receiving team.

## Known limitations

- A study aid, not an official ruling. Not for live games.
- Answers come only from the 6 rule sections search finds. If the right rule is not among them, the model says the rules don't cover it, or reasons from the wrong rule.
- The checks confirm that cited rules and the quote come from the retrieved text. They do not prove the reasoning is right.
- Free tiers have rate limits. When a provider is rate-limited, the app says it is unavailable instead of waiting; switch models in the sidebar.
- Questions to Groq and OpenRouter leave your machine. Use Ollama to keep them local.
- Text only, English only, NCAA rules only.

See section 8 of the [report](docs/report.md) for details.
