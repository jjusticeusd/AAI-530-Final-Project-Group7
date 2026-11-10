# Final Project Schedule: NCAA Football Referee Assistant (Group 7)

Team: Jason Justice (team lead, build), Timothy Hays (football rules and evaluation). Full plan: `docs/plan.md` in the team repo.

Target: project done Mon 11/30 (end of Module 6). Canvas due date: Mon 12/7, 11:59 PM PT. Each week ends Monday at 11:59 PM PT.

Team split is still open. Each week lists tasks for both options:
- **Option 1:** Jason builds, Timothy owns the rules and the eval.
- **Option 2:** pair on everything.

## Module 3: now to Mon 11/9

| Task | Option 1 | Option 2 |
|---|---|---|
| Pick the team split and confirm scope (rules Q&A plus described plays) | Both | Both |
| Find the official NCAA rulebook PDF and confirm the edition | Timothy | Both |
| Sign up for free API keys: Groq at https://console.groq.com/keys and OpenRouter at https://openrouter.ai/keys. Put them in `.env`, never in git | Timothy | Both |
| Set up the repo and rulebook pipeline: scaffold, backends from `playground/rules_referee.py`, rulebook download and ingest by rule number | Jason | Both |
| **Submit the M3 check-in** (Canvas survey, 5 pts) | Both | Both |

## Module 4: Tue 11/10 to Mon 11/16

| Task | Option 1 | Option 2 |
|---|---|---|
| Rule search, structured ruling, and citation check, working from the CLI | Jason | Both |
| Add embeddings to rule search and combine them with the keyword scores; rerun the 17 rule-search test questions | Jason | Both |
| System prompt v1, with one example ruling in the JSON format | Jason, Timothy reviews | Both |
| Draft 30-40 test questions with correct rulings: rules questions, described plays, penalties, edge cases, out-of-scope, judgment calls. Mark about a third as dev (used to fix prompts) and keep the rest as the test set | Timothy | Both |
| Extend the list of football slang and the rulebook words it maps to (lateral = backward pass, onside = free kick, OT = extra period, ...) so rule search finds the right sections | Timothy | Both |
| Ask the instructor whether the project needs model training, or whether prompting plus retrieval is enough | Jason | Jason |
| **Submit the M4 check-in** (goal, users, model, prompt strategy, AI tools, progress) **and the status form** (description, dataset: rulebook edition, pages, chunk count, test set size; meetings in the last two weeks; each member's contributions) | Both | Both |

## Module 5: Tue 11/17 to Mon 11/23

| Task | Option 1 | Option 2 |
|---|---|---|
| Streamlit app (chat, sidebar model picker, citations panel, review flag), run with uv | Jason | Both |
| Eval script and the first run on all models: each question 3 times, exact match on call/yards/spot, citation check, consistency, latency | Jason | Both |
| Write a 3-5 item grading rubric (correct, useful, clear, safe), grade the first run, and list the failures | Timothy | Both |
| Prompt v2 from the dev-set failures only, then save both runs | Both | Both |
| **Submit the M5 check-in.** Individual A5.1 is also due 11/23 | Both | Both |

## Module 6: Tue 11/24 to Mon 11/30 (Thanksgiving is 11/26)

| Task | Option 1 | Option 2 |
|---|---|---|
| Final eval on the test set and comparison table (hosted vs local: accuracy, citations, consistency, latency, cost, local model memory and quantization) | Jason | Both |
| Optional: an LLM judge scores the same answers; compare with Timothy's grades | Jason | Both |
| README and project documentation | Jason (tech), Timothy (users, football) | Both |
| Prompt and testing appendix | Both | Both |
| AI use and ethics reflection | Both | Both |
| Record the presentation (5 min or less intro, then 5 min or more demo) | Timothy leads the intro, Jason the demo | Both |
| **Submit the M6 check-in. The project is done.** Individual A6.1 is also due 11/30 | Both | Both |

## Module 7: Tue 12/1 to Mon 12/7 (buffer)

| Task | Option 1 | Option 2 |
|---|---|---|
| Fixes, re-record if needed, fresh-clone test of the README, and check the git history for keys or the PDF | Both | Both |
| Check every rubric item against `docs/Final_Project_71_Design_an_LLM_Application.md` in the team repo | Both | Both |
| **Submit the final project as team lead (12/7)** | Jason | Jason |
| **Submit the peer evaluation (12/7)** | Both | Both |

## Watch list

- The free API tiers have daily limits. Cache the eval results.
- Timothy's football schedule in late November.
- Don't evaluate on Approved Rulings that are also in the retrieval index.
- Peer evaluation scores equal contribution from the status form's contributions table. Keep a running log of who did what.
