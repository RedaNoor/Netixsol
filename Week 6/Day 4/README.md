# AFL LangGraph Application

Routes an AFL question to one of five paths — factual answer, data retrieval, match prediction,
player prediction, or refusal — through an explicit LangGraph, rather than leaving that decision
to a single agent's judgment on every turn.

## Setup

```bash
pip install -r requirements.txt
.env          # fill in OPENROUTER_API_KEY and GROQ_API_KEY
```

`data/` already has everything the retrieval and prediction tools need — feature tables, model
artifacts, and historical snapshots. No separate setup required.

## Project layout

```
state.py                State schema (query, history, intent, resolved entities, tool result,
                         validation status, final response)
graph.py                Graph assembly — nodes, conditional routing, memory checkpointer
nodes.py                Every node implementation (router, retrieval, prediction, direct_answer,
                         refusal, validation, clarification, response_formatter)
config.py                Router/direct-answer prompts, refusal message, prediction disclaimer,
                         clarification templates
entity_resolution.py     Team nickname/abbreviation resolution, relative-date handling
tools.py                 Structured retrieval functions (pandas — carried over from Day 3, plus
                         the 12 Day 3 lookup/leaderboard/roster tools)
langchain_tools.py       LangChain @tool wrappers around tools.py, used by the retrieval node
predict.py               Day 2's prediction models, adapted to this project's data/ layout
prediction_tools.py      LangChain @tool wrappers around predict.py, with entity resolution
                         baked in — used by the prediction node
explain.py                Prediction explanation — top driving factors, computed from real
                         permutation importance
run_chat.py               interactive CLI
tests/
  router_eval_prompts.py     Task 2 — 20 queries with expected intent
  run_router_eval.py         runs the router node alone, writes an accuracy table
  e2e_conversations.py       Task 5 — 10 conversations covering every path
  run_e2e_tests.py           runs all 10, with annotated state traces for 3 of them
reports/                     output lands here (reports/traces/ for the annotated ones)
```

## Running things

```bash
python run_chat.py                      # interactive
python tests/run_router_eval.py         # Task 2 deliverable — reports/router_accuracy.csv, .md
python tests/run_e2e_tests.py           # Task 5 deliverable — reports/e2e_summary.md, traces/
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
