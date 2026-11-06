# NCAA Football Referee Assistant: Final Project Plan (Group 7)

## Context
Final Project 7.1 (260 pts, due Mon 12/7 11:59 PM PT) asks for an applied LLM app with defined users, custom prompting, at least one context/eval/safety feature, test cases, docs, an AI/ethics reflection, and a 10-15 min recorded presentation with a demo of at least 5 min. Team: Jason ( Software Engineer) and Timothy Hays (active USD NCAA football player, domain expert). Target: done by end of Module 6 (Mon 11/30), with Module 7 as buffer.

Seed code: `ms-aai-530-jjustice/playground/rules_referee.py` already has a Groq / OpenRouter / Ollama backend picker, retry and cooldown handling, and a rules-vs-strategy system prompt with page citations. It stuffs the whole rulebook into the prompt, which works for board games but not for the roughly 200+ page NCAA rulebook. That is why RAG becomes the core feature. Novelty check (Nov 3): LLM sports work covers analytics and play-by-play; no rules-interpretation tool was found.

Decisions made:
- **Scope:** rules Q&A plus described-play rulings. Image/video plays are a stretch goal only.
- **Frontend:** Streamlit, run with uv and a setup script (no Docker: on macOS Docker gets no GPU, so Ollama runs natively either way).
- **Models:** free APIs and a local model, compared in the eval.
- **Rulebook:** a fetch script; the PDF is gitignored.
- **Repo:** public.
- **Course work:** the individual M5/M6 assignments stay separate from the project.

## What the app does
User types a question or describes a play. The pipeline:
1. **Retrieve** the relevant rule sections from the NCAA rulebook.
2. **Prompt** the model with a system prompt and the retrieved rules. It returns a structured ruling: call, foul (y/n), penalty yards, enforcement spot, cited rule numbers, confidence, and `needs_review`.
3. **Verify:** every cited rule number must appear in the retrieved text, otherwise the answer is flagged. Judgment calls that need video ("was it a catch?") get a "needs replay/official judgment" answer instead of a guess.

Users: fans, players, high school/youth officials studying the rules, broadcasters. It is not for live officiating; that goes in the ethics section.

## Repo scaffold (`AAI-530-Final-Project-Group7`)
```
README.md                 purpose, setup, models, env vars, limitations
pyproject.toml / uv.lock  uv-managed, bare package names
.env.example              GROQ_API_KEY, OPENROUTER_API_KEY, OLLAMA_URL
setup.sh                  installs uv if missing, uv sync, copies .env.example, fetches + ingests the rulebook, pulls the Ollama model if Ollama is installed
scripts/fetch_rulebook.py downloads the official PDF into data/ (gitignored)
src/referee/
  backends.py             ported from rules_referee.py (make_groq/make_openrouter/make_ollama, ask() retries)
  ingest.py               PDF -> chunks split on Rule/Section/Article numbers, keeps the rule id per chunk
  retrieve.py             embeddings + cosine over ~1-2k chunks (numpy is enough, no vector DB); add keyword match for rule numbers if recall is weak
  referee.py              retrieve -> prompt -> structured ruling -> verify
  prompts/                system prompt versions (v1, v2, ...) kept for the appendix
app/streamlit_app.py      chat, sidebar model picker, retrieved-rules/citations panel, review flag
eval/scenarios.csv        Timothy's plays + correct rulings (call, yards, rule)
eval/run_eval.py          runs every scenario x model; accuracy, citation validity, latency
eval/results/             saved runs per prompt version (iteration evidence)
docs/                     documentation, prompt/testing appendix, AI + ethics reflection, slides
```
Check current APIs with context7 when building: Streamlit, the Groq SDK, the OpenRouter SDK, the Ollama API, and the embedding library.

## Model options
| Role | Options |
|---|---|
| Hosted free API | Groq `openai/gpt-oss-120b` / `gpt-oss-20b`; OpenRouter `:free` models from the prototype list (re-check availability at build time; free tiers change) |
| Local (Mac, 24 GB unified) | Ollama 12-20B class: `gemma3:12b`, `qwen3:14b`, `gpt-oss:20b`; structured output via Ollama `format` JSON schema |
| Stretch: images | A free vision model on OpenRouter (e.g. a `-vl` model) for screenshot plays |
| Embeddings | Small local sentence-transformers model (free, offline) |

The eval compares hosted vs local on accuracy, citation validity, latency, and cost. That maps to MLO 1 and MLO 3 and fills the deployment-tradeoff section of the docs.

## Presentation layer options
- **Streamlit, run with uv (chosen).** Chat bubbles, with the model picker in a sidebar and a citations panel. `./setup.sh` once, then `uv run streamlit run app/streamlit_app.py`. Without Ollama, the picker shows only the API models. Chosen over Gradio after trying both on the playground referee: the layout looks more like a finished app, and chat history is easy to reset (switching games or pressing New chat starts fresh).
- **Optional extras if time allows:** host on Streamlit Community Cloud (free, deploys from the public GitHub repo, API backends only) for a public link; a Discord bot front end (reuses the llmcord idea) as future work.

## Team split (pick one)
| | Option 1: Jason builds, Timothy owns rules + eval | Option 2: pair on everything |
|---|---|---|
| Jason | Repo, ingest/RAG, backends, Streamlit app, setup script, eval harness | Same code, done in shared sessions; Timothy reviews each PR |
| Timothy | 30-40 scenario test set with correct rulings, judges outputs, writes the football/user sections, leads the presentation intro | Co-writes prompts and scenarios; builds some components himself |
| Pros | Fastest; plays to strengths | Both can explain every component (the rubric requires the team to understand all parts) |
| Cons | Timothy must still be able to explain the code in the demo | Slower; scheduling around football season |

## Schedule (week = Canvas module, ends Monday 11:59 PM PT)
| Week | Dates | Project work | Due |
|---|---|---|---|
| M3 | now - Mon 11/9 | Lock scope + team split; confirm rulebook PDF source and edition with Timothy; scaffold repo, port backends, fetch script + ingest | **Check-in #1 (11/9)**: goal, users, models, prompt strategy, AI tools, progress |
| M4 | 11/10 - 11/16 | RAG + structured ruling + verify working from CLI; system prompt v1; Timothy drafts scenarios (rules Q&A, penalties, edge cases, out-of-scope, judgment calls) | Check-in + status form |
| M5 | 11/17 - 11/23 | Streamlit UI + setup script; first eval run on all models; revise the prompt to v2 based on failures; save both runs | Check-in |
| M6 | 11/24 - 11/30 (Thanksgiving 11/26) | Final eval + comparison table; README, documentation, appendix, AI/ethics reflection; record the presentation (under 5 min intro, at least 5 min demo of a real scenario) | Check-in; **project done** |
| M7 | 12/1 - 12/7 | Buffer: fixes, re-record if needed, clean the repo, peer evaluation | **Final + peer eval (12/7)** |

Risks to check early:
- **Rulebook:** confirm the PDF is freely downloadable and which edition (NCAA football rules run in 2-year cycles).
- **Eval leakage:** the book's Approved Rulings (A.R.) are great ground truth, but if they're also in the index the test is leaky. Hold them out of retrieval for eval, or have Timothy write fresh plays.
- **Free tiers:** daily caps can stall eval runs. Cache results and keep the local model as a fallback.

## Verification
- `uv run python scripts/fetch_rulebook.py` and then ingest: spot-check 5 chunks to confirm the rule ids are correct.
- CLI ruling on 3 known A.R. plays from each backend. The JSON should parse, and the citations should pass verification.
- `./setup.sh` then `uv run streamlit run app/streamlit_app.py`: the app loads; one API model and one Ollama model each answer.
- `uv run python eval/run_eval.py`: results CSV per model and prompt version; Timothy signs off on the correct rulings.
- Before submitting: README fresh-clone test, no keys or PDF in git history, all rubric items checked against `Final_Project_71_Design_an_LLM_Application.md`.
