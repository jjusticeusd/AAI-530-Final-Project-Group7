# Final Project Schedule: NCAA Football Referee Assistant (Group 7)

Team: Jason Justice (team lead, build), Timothy Hays (football rules and evaluation). Full plan: `final_project_plan.md`.

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
| Set up the repo and rulebook pipeline: scaffold, `setup.sh`, backends from `playground/rules_referee.py`, fetch script, ingest by rule number | Jason | Both |
| **Submit check-in:** goal, users, models, prompt strategy, AI tools, progress | Both | Both |

## Module 4: Tue 11/10 to Mon 11/16

| Task | Option 1 | Option 2 |
|---|---|---|
| Rule search, structured ruling, and citation check, working from the CLI | Jason | Both |
| System prompt v1 | Jason, Timothy reviews | Both |
| Draft 30-40 test plays with correct rulings: rules questions, penalties, edge cases, out-of-scope, judgment calls | Timothy | Both |
| **Submit check-in and the status form** | Both | Both |

## Module 5: Tue 11/17 to Mon 11/23

| Task | Option 1 | Option 2 |
|---|---|---|
| Streamlit app (chat, sidebar model picker, citations panel, review flag), run with uv | Jason | Both |
| Eval script and the first run on all models | Jason | Both |
| Grade the first run and list the failures | Timothy | Both |
| Prompt v2 from those failures, then save both runs | Both | Both |
| **Submit check-in** | Both | Both |

## Module 6: Tue 11/24 to Mon 11/30 (Thanksgiving is 11/26)

| Task | Option 1 | Option 2 |
|---|---|---|
| Final eval and comparison table (hosted vs local: accuracy, citations, latency, cost) | Jason | Both |
| README and project documentation | Jason (tech), Timothy (users, football) | Both |
| Prompt and testing appendix | Both | Both |
| AI use and ethics reflection | Both | Both |
| Record the presentation (5 min or less intro, then 5 min or more demo) | Timothy leads the intro, Jason the demo | Both |
| **Submit check-in. The project is done.** | Both | Both |

## Module 7: Tue 12/1 to Mon 12/7 (buffer)

| Task | Option 1 | Option 2 |
|---|---|---|
| Fixes, re-record if needed, fresh-clone test of the README, and check the git history for keys or the PDF | Both | Both |
| Check every rubric item against `docs/canvas/assignments/Final_Project_71_Design_an_LLM_Application.md` | Both | Both |
| **Submit the final project as team lead (12/7)** | Jason | Jason |
| **Submit the peer evaluation (12/7)** | Both | Both |

## Watch list

- The free API tiers have daily limits. Cache the eval results.
- Timothy's football schedule in late November.
- Don't evaluate on Approved Rulings that are also in the retrieval index.
