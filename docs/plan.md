# NCAA Football Referee Assistant: Final Project Plan (Group 7)

## Context
Final Project 7.1 (260 pts, due Mon 12/7 11:59 PM PT) asks for an applied LLM app with defined users, custom prompting, at least one context/eval/safety feature, test cases, docs, an AI/ethics reflection, and a 10-15 min recorded presentation with a demo of at least 5 min. Team: Jason ( Software Engineer) and Timothy Hays (active USD NCAA football player, domain expert). Target: done by end of Module 6 (Mon 11/30), with Module 7 as buffer.

Seed code: `ms-aai-530-jjustice/playground/rules_referee.py` already has a Groq / OpenRouter / Ollama backend picker, retry and cooldown handling, and a rules-vs-strategy system prompt with page citations. It stuffs the whole rulebook into the prompt, which works for board games but not for the roughly 200+ page NCAA rulebook. That is why RAG becomes the core feature. Novelty check (Nov 3): LLM sports work covers analytics and play-by-play; no rules-interpretation tool was found.

Decisions made:
- **Scope:** rules Q&A plus described-play rulings. Image/video plays are a stretch goal only.
- **Frontend:** Streamlit, run with uv (no Docker: on macOS Docker gets no GPU, so Ollama runs natively either way).
- **Models:** free APIs and a local model, compared in the eval.
- **Rulebook:** ingest downloads it; the PDF is gitignored.
- **Repo:** public.
- **Course work:** the individual M5/M6 assignments stay separate from the project.
- **No fine-tuning (to confirm with the instructor).** The course says to try prompting and retrieval before training, and to fine-tune only when they can't reach the needed reliability. Our misses so far are rule-search misses, the 30-40 test questions are eval data, not training data, and the rules change every two years. The system prompt plus retrieval is how we shape behavior; the docs explain this choice. The course overview talk mentions "a training of some sort" while the written spec does not, so ask the instructor in M4.

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
src/referee/
  backends.py             ported from rules_referee.py (make_groq/make_openrouter/make_ollama, ask() retries)
  ingest.py               downloads the PDF into data/ (gitignored), then PDF -> chunks split on Rule/Section/Article numbers, keeps the rule id per chunk
  retrieve.py             keyword search over 473 chunks (BM25, rule-number boost, typo fix, slang-to-rulebook word list), then add embeddings and combine both scores (hybrid); numpy is enough, no vector DB
  referee.py              retrieve -> prompt -> structured ruling -> verify
  prompts/                system prompt versions (v1, v2, ...) kept for the appendix; each includes one example ruling in the JSON format
app/streamlit_app.py      chat, sidebar model picker, retrieved-rules/citations panel, review flag
eval/scenarios.csv        Timothy's test questions + correct rulings (call, yards, rule); split into a dev set (used to revise prompts) and a test set (final scoring only)
eval/run_eval.py          runs every question x model 3 times; exact match on call/yards/spot, citation validity, consistency across runs, latency
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

The eval compares hosted vs local on accuracy, citation validity, consistency, latency, and cost. Timothy also grades each answer with a 3-5 item rubric (correct, useful, clear, safe for the intended user), which covers the spec's usefulness and audience-fit criteria. Optional: an LLM judge scores the same answers, compared against Timothy's scores. The deployment section also notes the local models' memory needs and the 4-bit quantization Ollama uses. That maps to MLO 1, MLO 3, and the M7 deployment outcomes.

## Presentation layer options
- **Streamlit, run with uv (chosen).** Chat bubbles, with the model picker in a sidebar and a citations panel. `uv run python -m referee.ingest` once, then `uv run streamlit run app/streamlit_app.py`. The picker shows only the providers that are set up (a key in `.env`, or Ollama running). Chosen over Gradio after trying both on the playground referee: the layout looks more like a finished app, and chat history is easy to reset (switching games or pressing New chat starts fresh).
- **Optional extras if time allows:** host on Streamlit Community Cloud (free, deploys from the public GitHub repo, API backends only) for a public link; a Discord bot front end (reuses the llmcord idea) as future work.

## Team split (pick one)
| | Option 1: Jason builds, Timothy owns rules + eval | Option 2: pair on everything |
|---|---|---|
| Jason | Repo, ingest/RAG, backends, Streamlit app, eval harness | Same code, done in shared sessions; Timothy reviews each PR |
| Timothy | 30-40 scenario test set with correct rulings, judges outputs, writes the football/user sections, leads the presentation intro | Co-writes prompts and scenarios; builds some components himself |
| Pros | Fastest; plays to strengths | Both can explain every component (the rubric requires the team to understand all parts) |
| Cons | Timothy must still be able to explain the code in the demo | Slower; scheduling around football season |

## Schedule (week = Canvas module, ends Monday 11:59 PM PT)
| Week | Dates | Project work | Due |
|---|---|---|---|
| M3 | now - Mon 11/9 | Lock scope + team split; confirm rulebook PDF source and edition with Timothy; scaffold repo, port backends, rulebook download + ingest | **M3 check-in (11/9)**: Canvas survey, 5 pts |
| M4 | 11/10 - 11/16 | RAG + structured ruling + verify working from CLI; system prompt v1; add embeddings to rule search; Timothy drafts test questions (rules Q&A, penalties, edge cases, out-of-scope, judgment calls), split into dev and test, and extends the slang-to-rulebook word list for rule search; ask the instructor about training | **M4 check-in (11/16)**: goal, users, model, prompt strategy, AI tools, progress. **Status form**: project description, dataset (rulebook edition, pages, chunk count, test set size), meetings in the last two weeks, each member's contributions |
| M5 | 11/17 - 11/23 | Streamlit UI; first eval run on all models; revise the prompt to v2 based on dev-set failures; save both runs | Check-in (individual A5.1 also due 11/23) |
| M6 | 11/24 - 11/30 (Thanksgiving 11/26) | Final eval on the held-out test set + comparison table; README, documentation, appendix, AI/ethics reflection; record the presentation (under 5 min intro, at least 5 min demo of a real scenario) | Check-in; **project done** (individual A6.1 also due 11/30) |
| M7 | 12/1 - 12/7 | Buffer: fixes, re-record if needed, clean the repo, peer evaluation | **Final + peer eval (12/7)** |

Risks to check early:
- **Rulebook:** confirm the PDF is freely downloadable and which edition (NCAA football rules run in 2-year cycles).
- **Eval leakage:** the book's Approved Rulings (A.R.) are great ground truth, but if they're also in the index the test is leaky. Hold them out of retrieval for eval, or have Timothy write fresh plays.
- **Free tiers:** daily caps can stall eval runs. Cache results and keep the local model as a fallback.
- **Peer evaluation:** one item scores whether each member contributed equally, based on the contributions table in the status form. Keep a running log of who did what.

## Verification
- `uv run python -m referee.ingest`: spot-check 5 chunks to confirm the rule ids are correct.
- CLI ruling on 3 known A.R. plays from each backend. The JSON should parse, and the citations should pass verification.
- `uv run python -m referee.ingest` then `uv run streamlit run app/streamlit_app.py`: the app loads; one API model and one Ollama model each answer.
- `uv run python eval/run_eval.py`: results CSV per model and prompt version; Timothy signs off on the correct rulings.
- Before submitting: README fresh-clone test, no keys or PDF in git history, all rubric items checked against `Final_Project_71_Design_an_LLM_Application.md`.
