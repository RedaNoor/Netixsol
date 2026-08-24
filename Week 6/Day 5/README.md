---
noteId: "3ff940d09f9111f1be04e92091ab93e6"
tags: []

---

# AFL Assistant — Capstone (Week 6, Day 5)

Full product build on top of Days 1–4: the LangGraph application, hardened, evaluated, wrapped
behind a FastAPI endpoint with a minimal chat UI, plus a monitoring plan and stakeholder-ready
reporting.

## Setup

```bash
pip install -r requirements.txt
.env          # then fill in OPENROUTER_API_KEY and GROQ_API_KEY
```

## Running things

```bash
python run_chat.py                        # interactive CLI
uvicorn api:app --reload --port 8000       # API + chat UI at http://localhost:8000
python tests/run_router_eval.py            # Task 2 (Day 4 carryover) — router accuracy table
python tests/run_injection_tests.py        # Task 1 — 6 prompt-injection test cases
python tests/run_eval_suite.py             # Task 2 — 27-case combined evaluation suite
```

`tests/run_eval_suite.py`'s `prediction_sanity` category runs directly against the trained model
with no API key required — it's genuinely executed every time you run it, not just a canned
result. The other three categories (`factual_qa`, `scope_guardrail`, `multiturn_coherence`) need
a live LLM call.

## API reference

**POST /chat**
```json
{"message": "who won the 2024 grand final", "conversation_id": "optional-string"}
```
Returns:
```json
{"response": "...", "intent": "retrieval", "tools_called": ["round_matches"],
 "is_prediction": false, "conversation_id": "...", "latency_ms": 842.1}
```
`conversation_id` is caller-supplied and maps directly to the graph's `thread_id` — reuse it
across calls to keep conversation memory. Omit it and a new one is generated per call (no memory
across separate requests).

**GET /health** — liveness check, returns `{"status": "ok"}`.

Interactive API docs (Swagger UI) are auto-generated at `http://localhost:8000/docs` once the
server is running.

## What Day 5 added on top of Days 1–4

- **`safety.py`** — a `safe_node` decorator on every graph node (catches exceptions and timeouts
  gracefully instead of crashing a request) and `call_with_timeout` wrapping every LLM and tool
  call (12s tool timeout, 20s LLM timeout by default). Off-topic attempts are tracked per
  conversation thread; four or more in a row adds an escalation note to the refusal message.
- **`config.py`** — router prompt hardened against prompt-injection framing (fake system
  messages, embedded "ignore previous instructions," role-play reframing to an unrestricted
  persona); disclaimer wording tightened to "predicted probability, not a certainty."
- **`api.py`** — FastAPI `/chat` endpoint (`message` + `conversation_id` in, response +
  intent + tools called + latency out), a basic in-memory rate limiter (20 requests/60s per
  conversation), and a `/health` endpoint. `static/index.html` is a single-file chat UI with no
  build step, served directly by FastAPI.
- **`logging_setup.py`** — structured JSON request logging (query, intent, tools called,
  latency, token usage when the provider reports it) — the direct input to `MONITORING.md`.
- **`tests/injection_prompts.py` / `run_injection_tests.py`** — 6 prompt-injection variants
  (direct override, fake system message, role-play reframing, task-wrapped indirection, prompt
  extraction, injection nested inside quoted text).
- **`tests/eval_suite.py` / `run_eval_suite.py`** — the 27-case combined evaluation suite.
- **`MONITORING.md`** — one-page monitoring checklist and the weekly retrain-trigger loop.
- **`Executive_Report.pdf`** — 2-page stakeholder report.
- **`DEMO_SCRIPT.md`** — 5–7 minute demo script and slide outline.

## Project layout (full)

```
state.py, graph.py, nodes.py, config.py         Day 4 LangGraph core
entity_resolution.py, tools.py, langchain_tools.py, predict.py, prediction_tools.py, explain.py
                                                  Day 3/4 retrieval + prediction layer
safety.py                                        Day 5 — timeouts, error handling, abuse tracking
api.py, logging_setup.py                         Day 5 — FastAPI wrapper + structured logging
static/index.html                                Day 5 — minimal chat UI
run_chat.py                                      interactive CLI
tests/
  router_eval_prompts.py, run_router_eval.py         Day 4 — router accuracy (20 cases)
  e2e_conversations.py, run_e2e_tests.py             Day 4 — 10 conversations, annotated traces
  injection_prompts.py, run_injection_tests.py       Day 5 — 6 prompt-injection cases
  eval_suite.py, run_eval_suite.py                   Day 5 — 27-case combined evaluation
reports/                                          all eval output lands here
MONITORING.md, Executive_Report.pdf, DEMO_SCRIPT.md  Day 5 stakeholder deliverables
```

## Task 1 — why explicit routing instead of one agent deciding freely

A single agent with all these tools bound would have to *decide*, on every single turn, whether
to call a tool, which one, and — critically — whether the framing needs a probabilistic
disclaimer. That decision is made by the same probabilistic generation process as the rest of
its output, which means it can be skipped. A prediction response that forgets its disclaimer
isn't a hypothetical failure mode here — it's exactly the kind of thing that becomes a compliance
problem in a real deployment, and it's the reason the disclaimer isn't left to the LLM.

Concretely, in this codebase:

- **The disclaimer is structural, not requested.** `response_formatter_node` appends
  `config.PREDICTION_DISCLAIMER` in code, unconditionally, whenever `intent` is
  `prediction_match`/`prediction_player` — see `nodes.py`. There's no prompt instruction the
  model could forget to follow, because the model never gets the choice.
- **The refusal is structural too.** `refusal_node` returns `config.REFUSAL_MESSAGE` directly —
  no LLM call at all on that path. An off-topic request can't be talked out of a refusal because
  nothing generative sits between "off-topic" and the response.
- **Routing is auditable.** The router's job is narrowly "classify this one thing," which is a
  much smaller, more evaluable task than "decide everything about how to respond" — Task 2's
  accuracy table only makes sense because routing is a discrete, gradeable step rather than
  folded into one big generation.
- **Validation is a real checkpoint, not a hope.** `validation_node` runs after every
  retrieval/prediction call and explicitly checks for a tool error before anything gets
  formatted into a response — a single agent can call a tool, get an error back, and still
  narrate an answer around it if nothing forces a check.

### The graph

```
START -> ingest -> router -> [direct_answer | retrieval | prediction | refusal | clarification]
                                    |              |            |
                                    v              v            v
                                (finalize)    validation    validation
                                                   |             |
                                        [clarification | response_formatter]
                                                   |             |
                                              (finalize)    (finalize) -> END
```

`ingest` appends the new user message to history before anything else runs, so every downstream
node reads a consistent view of the conversation. `finalize` appends the assistant's response
after everything else runs, so the checkpointer persists exactly one full turn per invocation —
this is also what makes multi-turn memory work: the next `invoke()` call on the same `thread_id`
starts with the full prior history already in state.

## Task 3 — entity resolution ("will the Pies beat the Cats this week")

Two problems, both handled in code the LLM doesn't have to get right on its own:

- **Nicknames**: `entity_resolution.resolve_team()` maps common nicknames and abbreviations
  ("Pies", "Cats", "Dogs", "GWS", "Freo", ...) to the dataset's exact team names, with a
  substring-match fallback and an official-name normalizer underneath. If nothing resolves, it
  raises `TeamResolutionError` with suggestions rather than guessing — this is what routes to
  clarification instead of a wrong prediction.
- **"This week"**: there's no future-fixture list in this dataset, so `resolve_date()` doesn't
  pretend to find a real scheduled match. A relative reference falls back to each team's most
  recently known form (as of the dataset's latest date) and returns an explicit note explaining
  that substitution — the note ends up in the final response, not hidden.

Every prediction response includes `explanation`: the top 3 features the model leans on most in
general (from a real permutation-importance run over the held-out season, see `explain.py`),
paired with this specific matchup's actual values on each. This is deliberately framed as "here's
what the model weighs most, and here's where this matchup lands on those factors" rather than a
claimed causal attribution for this one prediction — a true per-prediction attribution would need
something like SHAP, which isn't part of this project's model stack, and overclaiming precision
here would be worse than the honest, slightly less granular version.

## Task 4 — validation and fallbacks

`validation_node` is the single place that decides whether a tool result is trustworthy enough to
turn into a formatted response. It checks for `tool_error` and `resolution_errors`, and branches
on `error_type` to generate a specific, useful clarification question rather than a generic "I
didn't understand":

| error_type | What triggered it | Clarification asked |
|---|---|---|
| `team_resolution` | Team name/nickname didn't match anything | Names the unresolved text, offers suggestions if any exist |
| `same_team` | Both sides of a prediction resolved to the same team | States the conflict directly |
| `unsupported_stat` | Asked to predict a stat with no trained model (e.g. tackles) | Offers the two things that *are* supported (fantasy points fully, disposals/goals as a rolling-average estimate) |

An unsupported-stat request is the concrete "genuinely unsupported query" case from the task: ask
to predict something like tackles, and the system says plainly that it isn't modeled, rather than
inventing a number that looks like a real prediction.

## Comparing this to a single monolithic LangChain agent

A single agent binding all 14 tools (12 retrieval + 2 prediction) has to re-derive, from the
prompt alone, on every turn: which tool family is even relevant, whether this is a stats question
or a prediction question, and whether the answer needs a disclaimer — three judgment calls
collapsed into one generation step, each independently able to go wrong with no checkpoint in
between. Splitting them into router → validation → formatter turns each of those into a separate,
individually testable, individually fixable unit — the router accuracy table in
`reports/router_accuracy.csv` is only possible because routing is its own step, and the
disclaimer/refusal guarantees only hold because they're code, not prompt instructions competing
for the model's attention alongside everything else it's trying to do in one shot.
