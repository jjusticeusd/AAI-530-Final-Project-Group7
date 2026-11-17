# NCAA Football Referee

AAI-530 Final Project, Group 7: Jason Justice and Timothy Hays.

Ask an NCAA football rules question or describe a play, and get a ruling that cites rule numbers from the official 2026 NCAA Football Rules and Interpretations. Work in progress.

## Setup

Works on macOS and Windows.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Get at least one model backend:
   - A free Groq API key: https://console.groq.com/keys (fastest), or
   - A free OpenRouter API key: https://openrouter.ai/keys, or
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

## Evaluate

Rule search only (no model calls, free):
```
uv run python eval/retrieval_eval.py
```

Rulings from the models. By default the eval uses one model per provider: Groq `openai/gpt-oss-120b`, OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free`, and Ollama `gemma3:12b`. Each question runs 3 times per model. Answers are saved to `eval/results/` as they come in, so a run stopped by a free-tier limit picks up where it left off:
```
uv run python eval/run_eval.py --split dev
uv run python eval/run_eval.py --split dev --models "Groq / openai/gpt-oss-120b"
uv run python eval/run_eval.py --split dev --summary
```

## Layout

- `referee/backends.py`: Groq, OpenRouter, and Ollama clients with retries. Only providers that are set up are offered.
- `referee/ingest.py`: downloads the official PDF (not stored in this repo) and splits it into rule chunks (like `9-1-2`) and approved-ruling chunks (like `A.R. 9-1-2`).
- `referee/retrieve.py`: keyword search (BM25) over the chunks, with a rule-number boost, typo fixes, and a football slang list.
- `referee/ruling.py`: searches the rules, asks the model for a JSON ruling, and checks that every cited rule number was in the retrieved rules and that the quote is word for word.
- `referee/prompts/`: system prompt versions.
- `referee/app.py`: the Streamlit chat app.
- `eval/retrieval.csv`, `eval/retrieval_eval.py`: 19 rule-search test questions and their scorer.
- `eval/scenarios.csv`: test questions with the expected ruling (foul, yards, spot, rule). `dev` questions are used to revise the prompt; `test` questions are only for the final run.
- `eval/run_eval.py`: runs the scenarios on each model and scores type, foul, yards, spot, rule cited, citation check, quote, review flag, consistency across runs, and latency. Also writes a grading sheet for human review.
- `eval/results/`: saved model answers (one JSONL file per prompt and model), plus the generated summary table and grading sheet.
- `docs/appendix.md`: prompt and testing appendix.
- `docs/planning/`: the assignment spec, plan, and schedule.
