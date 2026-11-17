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

## Layout

- `src/referee/backends.py`: Groq, OpenRouter, and Ollama clients with retries. Only providers that are set up are offered.
- `src/referee/ingest.py`: downloads the official PDF (not stored in this repo) and splits it into rule chunks (like `9-1-2`) and approved-ruling chunks (like `A.R. 9-1-2`).
- `docs/`: assignment spec, plan, and schedule.
