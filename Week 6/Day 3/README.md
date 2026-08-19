# AFL Chat Agent

A domain-scoped conversational agent for AFL teams, players, matches, and stats. Every number
it states comes from a real lookup against the dataset — never from the model's memory.

## Setup

```bash
pip install -r requirements.txt

```

The `data/` folder already contains the feature tables and player info the tools query against.
No database setup is required.

## Project layout

```
config.py               system prompt, scope definition, refusal examples
tools.py                structured query functions (pandas lookups — exact numbers, no LLM)
knowledge_base.py       derived match-description corpus + FAISS vector store (semantic search)
langchain_tools.py      LangChain @tool wrappers around tools.py and knowledge_base.py
grounding.py            logs tool calls and cross-checks answer numbers against them
agent.py                builds the tool-calling agent with per-session conversation memory
run_chat.py             interactive CLI — talk to the agent directly
build_match_details.py  derives data/match_details.parquet from the raw match CSV (already run —
                         included for reproducibility, not something you need to re-run)
data/                    feature tables, player bios, and match detail the tools query against
tests/
  adversarial_prompts.py    Task 1 — 10 scope/jailbreak-style prompts
  guardrail_prompts.py      Task 5 — 21 prompts (legitimate / off-topic / ambiguous)
  run_guardrail_eval.py     runs both sets against the live agent, writes reports/
  multiturn_demo.py         Task 4 — scripted 5-turn conversation testing context carry
reports/                    output of run_guardrail_eval.py lands here
```

## Running things

**Chat interactively:**
```bash
python run_chat.py
```

**Run the multi-turn conversation test:**
```bash
python tests/multiturn_demo.py
```

**Run the full guardrail evaluation** (adversarial + guardrail prompt sets, ~29 calls total):
```bash
python tests/run_guardrail_eval.py
```
This writes `reports/adversarial_results.csv`, `reports/guardrail_results.csv`, and
`reports/summary.md`. Every response gets an automated grounding check (do the numbers in the
answer trace back to a real tool call?) and, for off-topic prompts, a keyword-based first pass at
whether the response engaged with the off-topic content instead of declining. Neither check is a
substitute for reading the actual responses — the `manual_pass_fail` column in each CSV is there
for exactly that, and `summary.md` has a failure-pattern table to fill in once you've read through
the transcripts and decided what to fix.
