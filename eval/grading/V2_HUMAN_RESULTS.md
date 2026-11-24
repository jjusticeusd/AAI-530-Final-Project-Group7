# V2 human grading results

Timothy approved grades for all 53 available run-1 answers on November 23, 2026. These answer Jason’s historical 18 development questions; they are not final-test scores or results on the separate approved 40-case dataset. Groq d16 has no response and is excluded, not assigned zero. No new model calls were made.

## Human scores

Scores range from 1 to 3. Means are subjective rubric scores, not overall accuracy percentages. Full-credit correct counts require correct=3.

| Model | Answers | Correct mean | Useful mean | Clear mean | Safe mean | Correct=3 |
|---|---:|---:|---:|---:|---:|---:|
| Groq / openai/gpt-oss-120b | 17 | 2.18 | 2.12 | 2.41 | 2.18 | 7/17 |
| Ollama / gemma3:12b | 18 | 2.22 | 2.28 | 2.28 | 2.11 | 8/18 |
| OpenRouter / nvidia/nemotron-3-ultra-550b-a55b:free | 18 | 2.78 | 2.94 | 2.89 | 2.83 | 14/18 |

## Human versus saved LLM judge

All final human scores were supplied before this comparison. The AI-assisted suggestions were prepared without reading the saved judge scores; they were visible to Timothy, so these human ratings were assisted rather than fully blind independent ratings. The judge is a second opinion, not ground truth.

| Criterion | Paired answers | Exact agreement | Within one point | Human mean | Judge mean |
|---|---:|---:|---:|---:|---:|
| correct | 53 | 38/53 | 53/53 | 2.40 | 2.42 |
| useful | 53 | 40/53 | 52/53 | 2.45 | 2.53 |
| clear | 53 | 36/53 | 52/53 | 2.53 | 2.83 |
| safe | 53 | 39/53 | 51/53 | 2.38 | 2.64 |

## Scope

V1 human grading (48 saved answers) remains ungraded. These approved scores cover only v2 run 1, not all repeated runs. The 10 reserved final cases remain unused. Timothy resolved d08 against the pinned 2026 momentum exception: possession at own 3 followed by original momentum into the end zone returns the ball to the 3.
