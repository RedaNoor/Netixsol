# -*- coding: utf-8 -*-
"""
Converted from IPYNB to PY
"""

# %% [markdown] Cell 1
# # LangGraph: Stateful, Multi-Step & Cyclical Agent Workflows
# 
# **Workflow:** a *research assistant* that plans a query, retrieves documents, drafts an answer, critiques its own draft (looping back to revise if quality is too low), then pauses for **human approval** before a risky action (`send_report`), with full **persistence** and **time-travel debugging**.
# 
# **LLM provider:** OpenRouter as the primary provider, with Groq as an automatic fallback if OpenRouter errors out (rate limit, outage, etc). This is implemented with LangChain's `.with_fallbacks()` on the `Runnable` interface, the same LCEL concept from Day 2, just used to chain two providers instead of chaining prompt -> model -> parser.
# 
# To use Groq only instead of the OpenRouter-primary setup, no restructuring is needed. In the LLM setup cell, comment out the `.with_fallbacks(...)` line and uncomment the `llm = groq_llm` line directly below it. Nothing else in the notebook needs to change.
# 
# **Search provider:** Tavily's search API for the `retrieve` node, wrapped in a real `@tool`-decorated function following the Day 2 `@tool` convention.

# %% [code] Cell 2
#%pip install langgraph langchain-core langchain-openai langchain-groq tavily-python python-dotenv

# %% [markdown] Cell 3
# ## Task 1 - Graph Concepts & State Design
# 
# ### Core building blocks
# 
# | Concept | What it is | Analogy to Day 1/Day 2 |
# |---|---|---|
# | **`StateGraph`** | The graph builder. You register nodes and edges on it, then `.compile()` it into a runnable graph. | Replaces the manual `while` loop that drove the raw-Python agent. |
# | **State** | A single shared `TypedDict` (or Pydantic model) that every node reads from and writes to. Each key can have a **reducer** (e.g. `Annotated[list, operator.add]`) controlling how a node's partial update is *merged* into the existing state, instead of overwriting it. | Directly analogous to the message list we hand-built as `agent_scratchpad` on Day 1, except LangGraph generalizes it to *any* piece of state, not just messages. |
# | **Node** | A plain Python function `(state) -> dict`. It receives the current state and returns a **partial update** (only the keys it changed). | Equivalent to one "step" in the ReAct loop, a Reason, an Act, or an Observe, made explicit as its own function. |
# | **Edge** | A fixed transition `add_edge("a", "b")`, always go from `a` to `b`. | Analogous to always calling the next hard-coded step in a linear script. |
# | **Conditional edge** | `add_conditional_edges("a", router_fn, {"x": "x", "y": "y"})`, after node `a` runs, call `router_fn(state)` and its return value picks the next node. This is what makes **branching and cycles** possible. | This is the part a plain `AgentExecutor` cannot express cleanly, see Task 3. |
# 
# ### State schema for the research-assistant workflow
# 
# We use a `TypedDict` (LangGraph's most common state type, lighter weight than a Pydantic model, though Pydantic is a reasonable choice too when you want runtime validation on every node's return value). `log` uses the `operator.add` reducer so every node's log line is **appended** to a running list instead of overwriting the previous one. This is the key structural idea a plain dict update doesn't give you for free.

# %% [code] Cell 4
import operator
from typing import TypedDict, Annotated, List, Optional

class ResearchState(TypedDict):
    topic: str                                    # the user's question / research topic
    plan: str                                      # search plan produced by `plan`
    documents: List[str]                           # retrieved snippets
    draft: str                                      # current draft answer
    critique_feedback: str                          # feedback from the last critique pass
    quality_score: int                              # 0-10 score from `critique`
    retry_count: int                                # how many generate->critique passes have run
    max_retries: int                                # cap to guarantee termination of the loop
    approved: Optional[bool]                        # human decision at the interrupt point
    final_output: str                               # the final formatted / sent output
    log: Annotated[List[str], operator.add]         # reducer: append, don't overwrite

# %% [markdown] Cell 5
# ### Graph diagram (planned before coding)
# 
# ```
#         START
#           |
#           v
#         [plan]
#           |
#           v
#       [retrieve]
#           |
#           v
#       [generate] <----------------+
#           |                       |
#           v                       |
#       [critique] --(score<7 and retries<max)--+
#           |
#    (score>=7 or retries==max)
#           |
#           v
#    [human_approval]  <-- interrupt(): pauses for a human decision
#       |         \\
#   (approved)   (rejected)
#       |             \\
#       v               v
#  [send_report]     [aborted]
#       |               |
#       +------> END <--+
# ```
# 
# This is the exact shape we build up in Tasks 2-4: a **linear spine** (`plan -> retrieve -> generate`), a **cycle** (`generate <-> critique`), and a **branch with a pause** (`human_approval -> send_report | aborted`).

# %% [markdown] Cell 6
# ## Setup: LLM Provider (OpenRouter -> Groq Fallback) & Tavily Search Tool
# 
# Two things every node below depends on:
# 
# 1. **`llm`**, a chat model `Runnable`. `ChatOpenAI` pointed at OpenRouter's OpenAI-compatible endpoint is the primary, `ChatGroq` is chained on with `.with_fallbacks()` so if OpenRouter raises an exception (timeout, rate limit, provider outage), LangChain automatically retries the same call on Groq instead of failing the node. To use Groq only, comment out the `.with_fallbacks(...)` line and uncomment the plain `llm = groq_llm` line right below it, nothing else needs to change.
# 2. **`retrieve_documents`**, a real `@tool`-decorated function wrapping `TavilyClient.search()` for the `retrieve` node, following the same `@tool` decorator convention from Day 2. Tavily requires a `TAVILY_API_KEY` (free tier available). Results are truncated per source before they reach any prompt, since raw Tavily content can include long irrelevant boilerplate that adds noise without adding signal.
# 
# Swap `OPENROUTER_MODEL` / `GROQ_MODEL` for whatever models your accounts have access to.

# %% [code] Cell 7
import os
from dotenv import load_dotenv

load_dotenv()  # loads OPENROUTER_API_KEY / GROQ_API_KEY / TAVILY_API_KEY from a .env file, if present

OPENROUTER_MODEL = "openai/gpt-4o-mini"        # any model slug available on your OpenRouter account
GROQ_MODEL = "llama-3.3-70b-versatile"         # any model available on your Groq account

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")   # only required if using OpenRouter as primary
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise EnvironmentError(
        "Missing GROQ_API_KEY or TAVILY_API_KEY. Both are required regardless of which LLM path you use."
    )
if not OPENROUTER_API_KEY:
    print("OPENROUTER_API_KEY not set. This is fine if you switch to the Groq-only line in the next cell.")

# %% [code] Cell 8
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

openrouter_llm = ChatOpenAI(
    model=OPENROUTER_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.3,
)

groq_llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

# Primary/backup pattern via LCEL: same Runnable interface, automatic failover on error.
llm = openrouter_llm.with_fallbacks([groq_llm])

# To use Groq only (no OpenRouter dependency at all): comment out the line above
# and uncomment the line below. Nothing else in the notebook needs to change.
# llm = groq_llm

# %% [code] Cell 9
from tavily import TavilyClient
from langchain_core.tools import tool

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

MAX_CONTENT_CHARS = 500  # truncate each result so noisy/boilerplate pages don't dominate the prompt

@tool
def retrieve_documents(query: str) -> str:
    """Search the web for information relevant to the query using Tavily and return formatted results."""
    response = tavily_client.search(query=query, max_results=5)
    formatted_results = []
    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "No title")
        url = result.get("url", "")
        content = result.get("content", "No content available")[:MAX_CONTENT_CHARS]
        formatted_results.append(f"[{i}] Title: {title}\n    URL: {url}\n    Content: {content}\n")
    return "\n".join(formatted_results) if formatted_results else "No results found for the query."

# %% [markdown] Cell 10
# ## Task 2 - Build a Linear Graph
# 
# The plain 4-node linear graph: `plan -> retrieve -> generate -> format`. No branching yet, this establishes the baseline before we add cycles and interrupts in Tasks 3-4.
# 
# Each node is a small function that takes the whole `state` and returns **only the keys it is updating** (LangGraph merges this partial dict into the running state automatically).
# 
# `retrieve` builds its search query from `plan` (not just the raw topic). The plan node decides *what to look for*, and retrieval acts on that decision, mirroring how a planning step should actually inform the tool call that follows it.

# %% [code] Cell 11
def plan_node(state: ResearchState) -> dict:
    prompt = (
        f"In one sentence, write a concrete web-search plan for researching: '{state['topic']}'. "
        "State exactly what to search for."
    )
    plan = llm.invoke(prompt).content
    return {"plan": plan, "log": [f"[plan] {plan}"]}


def retrieve_node(state: ResearchState) -> dict:
    query = f"{state['topic']}: {state['plan']}"
    results = retrieve_documents.invoke({"query": query})
    documents = [results] if isinstance(results, str) else list(results)
    return {"documents": documents, "log": [f"[retrieve] query='{query}'"]}


def generate_node(state: ResearchState) -> dict:
    attempt = state.get("retry_count", 0) + 1
    feedback = state.get("critique_feedback", "")
    prompt = (
        f"Write a concise, well-organized answer about '{state['topic']}' using this research:\n\n"
        f"{state['documents']}\n"
    )
    if feedback:
        prompt += f"\nRevise your previous draft to address this feedback: {feedback}"
    draft = llm.invoke(prompt).content
    return {"draft": draft, "log": [f"[generate] attempt {attempt}: {draft[:70]}..."]}


def format_node(state: ResearchState) -> dict:
    final = f"FINAL ANSWER\n=============\n{state['draft']}"
    return {"final_output": final, "log": ["[format] finalized output"]}

print ("Setup complete. You can now run the research workflow using the defined nodes.")

# %% [code] Cell 12
def make_init_state(topic: str) -> ResearchState:
    """Build a fresh initial state dict with every ResearchState key populated."""
    return {
        "topic": topic,
        "plan": "",
        "documents": [],
        "draft": "",
        "critique_feedback": "",
        "quality_score": 0,
        "retry_count": 0,
        "max_retries": 2,
        "approved": None,
        "final_output": "",
        "log": [],
    }
print ("Setup complete. You can now run the research workflow using the defined nodes.")

# %% [code] Cell 13
from langgraph.graph import StateGraph, START, END

linear_builder = StateGraph(ResearchState)
linear_builder.add_node("plan", plan_node)
linear_builder.add_node("retrieve", retrieve_node)
linear_builder.add_node("generate", generate_node)
linear_builder.add_node("format", format_node)

linear_builder.add_edge(START, "plan")
linear_builder.add_edge("plan", "retrieve")
linear_builder.add_edge("retrieve", "generate")
linear_builder.add_edge("generate", "format")
linear_builder.add_edge("format", END)

linear_graph = linear_builder.compile()
print("Linear graph compiled with nodes:", list(linear_graph.get_graph().nodes))

# %% [markdown] Cell 14
# Run it and print the state **after every node**, to confirm each node's partial update is merged correctly:

# %% [code] Cell 15
init_state = make_init_state("LangGraph")

for i, snapshot in enumerate(linear_graph.stream(init_state, stream_mode="values")):
    print(f"--- state after step {i} ---")
    for k, v in snapshot.items():
        print(f"  {k}: {v}")
    print()

# %% [markdown] Cell 16
# ## Task 3 - Add Conditional Edges & Cycles
# 
# We insert a `critique` node after `generate`. A **conditional edge** decides, based on `quality_score` and `retry_count`, whether to loop back to `generate` (self-correction) or move on. `max_retries` in state guarantees the loop terminates even if quality never crosses the threshold, this matters more with a real LLM than it did with a scripted score, since a live model's output is genuinely non-deterministic from run to run.
# 
# `critique` uses **structured output** (a Pydantic model passed to `llm.with_structured_output`, same pattern as Day 2) instead of asking the model to format a score as free text, this keeps `quality_score` reliably parseable as an `int` every time.
# 
# A real critique score is not guaranteed to fall below the threshold on the first pass. To make sure the retry branch, its logging, and the checkpoint it creates are always demonstrated at least once, `FORCE_RETRY_DEMO` below overrides only the *score* used for routing on the first critique pass, the critique call itself is always real. Set it to `False` for a fully LLM-driven run with no override.

# %% [code] Cell 17
from pydantic import BaseModel, Field

class CritiqueResult(BaseModel):
    quality_score: int = Field(description="Quality score from 0 to 10, judging accuracy, clarity, and completeness.")
    feedback: str = Field(description="Concrete, actionable feedback if quality_score < 7; otherwise an empty string.")


structured_llm = llm.with_structured_output(CritiqueResult)

# Demonstration flag: forces the score on the FIRST critique pass only, so the retry
# branch (and the checkpoint it creates) is guaranteed to be shown at least once,
# regardless of how the real LLM happens to score the first draft. The critique call
# itself is always real, only the score used for routing on pass 1 is overridden.
FORCE_RETRY_DEMO = True

def critique_node(state: ResearchState) -> dict:
    attempt = state.get("retry_count", 0) + 1
    prompt = (
        f"Critique this draft answer about '{state['topic']}' for accuracy, clarity, and completeness.\n\n"
        f"Draft:\n{state['draft']}"
    )
    result: CritiqueResult = structured_llm.invoke(prompt)

    quality_score = result.quality_score
    feedback = result.feedback

    if FORCE_RETRY_DEMO and attempt == 1:
        quality_score = min(quality_score, 5)
        feedback = feedback or (
            "Demo override: forcing a below-threshold score on the first pass so the "
            "retry branch is demonstrated. Add more specific detail and cite the "
            "retrieved sources more directly."
        )

    return {
        "quality_score": quality_score,
        "critique_feedback": feedback,
        "retry_count": attempt,
        "log": [f"[critique] pass {attempt}: score={quality_score} feedback='{feedback}'"],
    }


def route_after_critique(state: ResearchState) -> str:
    """Conditional edge function: returns the NAME of the next node."""
    if state["quality_score"] >= 7 or state["retry_count"] >= state["max_retries"]:
        return "accept"
    return "revise"

# %% [markdown] Cell 18
# ### Conditional Routing
# 
# The critique node evaluates the generated answer and stores a quality score in the shared state. If the score is below the required threshold and retries remain, the graph routes to `revise`, which sends execution back to `generate`. If the answer meets the threshold or the retry limit has been reached, the graph continues to the human approval stage. The actual loop-back is demonstrated once the full graph is assembled and run in Task 4, its `log` output there shows each `[generate]`/`[critique]` pass.

# %% [markdown] Cell 19
# **Why this loop is awkward in a plain `AgentExecutor` but natural in LangGraph:** `AgentExecutor` runs a single fixed ReAct loop (Reason -> Act -> Observe -> repeat) driven internally by the executor. You cannot easily insert a *second*, differently-shaped loop (draft -> critique -> maybe-redraft) with its own exit condition and retry cap without hacking around the executor's control flow, for example by re-invoking it manually and hand-managing the retry counter yourself. LangGraph makes this trivial because control flow *is* the graph: a conditional edge is just a function returning a node name, so any loop shape, including nested or multiple independent loops, is expressed directly as graph structure instead of being smuggled through prompts or external retry code.

# %% [markdown] Cell 20
# ## Task 4 - Human-in-the-Loop & Interrupts
# 
# We add a `human_approval` node before the "risky" action (`send_report`, standing in for sending an email or making a purchase call). It calls LangGraph's `interrupt()` function, which pauses the graph **and returns control to the caller**, surfacing a payload describing what's about to happen. This is the modern, recommended pattern (LangChain, Dec 2024+) over the older static `interrupt_before=[...]` compile-time option. `interrupt()` lets you pause **inside** node logic based on a runtime condition, and pass structured context to the human reviewer.
# 
# Resuming happens via `graph.invoke(Command(resume=<value>), config)`, the resume value is returned from the `interrupt()` call, as if it had returned normally. The approve/reject decision itself is simulated below (standing in for whatever surfaces the pause to an actual human, a UI, a Slack message, a CLI prompt), the graph mechanics do not care where the decision comes from.
# 
# A **checkpointer is required** for interrupts to work at all, without one, LangGraph has nowhere to persist the paused state.

# %% [code] Cell 21
from langgraph.types import interrupt, Command

def human_approval_node(state: ResearchState) -> dict:
    decision = interrupt({
        "action": "send_report",
        "question": "Approve sending this report externally?",
        "draft_preview": state["draft"][:120],
    })
    return {
        "approved": bool(decision.get("approved", False)),
        "log": [f"[human_approval] approved={decision.get('approved', False)}"],
    }

def route_after_approval(state: ResearchState) -> str:
    return "send_report" if state["approved"] else "aborted"

def send_report_node(state: ResearchState) -> dict:
    # The "risky" action itself only ever runs after explicit human approval.
    final = f"REPORT SENT\n===========\n{state['draft']}"
    return {"final_output": final, "log": ["[send_report] risky action executed: report sent"]}

def aborted_node(state: ResearchState) -> dict:
    return {"final_output": "Report NOT sent (rejected by reviewer).", "log": ["[aborted] human rejected the action"]}

# %% [code] Cell 22
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

builder = StateGraph(ResearchState)
builder.add_node("plan", plan_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)
builder.add_node("critique", critique_node)
builder.add_node("human_approval", human_approval_node)
builder.add_node("send_report", send_report_node)
builder.add_node("aborted", aborted_node)

builder.add_edge(START, "plan")
builder.add_edge("plan", "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "critique")
builder.add_conditional_edges("critique", route_after_critique, {"revise": "generate", "accept": "human_approval"})
builder.add_conditional_edges("human_approval", route_after_approval, {"send_report": "send_report", "aborted": "aborted"})
builder.add_edge("send_report", END)
builder.add_edge("aborted", END)

full_graph = builder.compile(checkpointer=checkpointer)
print("Full graph compiled with nodes:", list(full_graph.get_graph().nodes))

# %% [markdown] Cell 23
# **Run 1: approve the action.** The graph runs until it hits `interrupt()`, then we resume with `Command(resume={"approved": True})`:

# %% [code] Cell 24
config = {"configurable": {"thread_id": "session-1"}}
init_state = make_init_state("LangGraph")

result = full_graph.invoke(init_state, config)
print("Graph paused. Interrupt payload:")
print(" ", result["__interrupt__"][0].value)

# %% [code] Cell 25
resumed = full_graph.invoke(Command(resume={"approved": True}), config)

print(resumed["final_output"])
print()
print("Full run log (self-correction loop is visible as repeated [generate]/[critique] pairs):")
for line in resumed["log"]:
    print(" ", line)

# %% [markdown] Cell 26
# **Run 2: reject the action**, on a fresh `thread_id` so it does not collide with `session-1`'s persisted state:

# %% [code] Cell 27
config2 = {"configurable": {"thread_id": "session-2"}}
init_state_2 = make_init_state("LangGraph")

full_graph.invoke(init_state_2, config2)                                    # runs to the interrupt
resumed2 = full_graph.invoke(Command(resume={"approved": False}), config2)  # resume, rejecting

print(resumed2["final_output"])

# %% [markdown] Cell 28
# ### When does a real product need human-in-the-loop vs full autonomy?
# 
# Human review earns its cost when an action is **hard to undo, externally visible, or expensive to get wrong**: sending an email to a customer, executing a financial transaction, deleting production data, or publishing content under an organization's name. It is also worth it when the model's confidence is genuinely uncertain (for example a low critique score) or the blast radius of a mistake is large relative to how often the workflow runs, so the review cost per run stays low.
# 
# Full autonomy is reasonable when actions are **cheap, reversible, and high-frequency**: read-only lookups, internal draft generation, sandboxed computations, or anything where a wrong step just gets corrected on the next loop iteration (like our `generate <-> critique` cycle, which is autonomous *by design*, a human only needs to step in once, right before the irreversible step).

# %% [markdown] Cell 29
# ## Task 5 - Persistence & Debugging
# 
# We already attached a `MemorySaver()` checkpointer above, that is what let `session-1` and `session-2` resume from exactly where they paused. Below we look at what persistence actually stores: a full history of state snapshots, one per "super-step" of the graph, which enables **time-travel debugging** via `get_state_history()`.

# %% [code] Cell 30
history = list(full_graph.get_state_history(config))   # config = session-1
print(f"Checkpoints recorded for session-1: {len(history)}\n")

# history is returned most-recent-first; reverse to walk it chronologically
for snap in reversed(history):
    print(
        f"step={snap.metadata.get('step')}, "
        f"next={snap.next}, "
        f"retry_count={snap.values.get('retry_count')}, "
        f"score={snap.values.get('quality_score')}"
    )

# %% [markdown] Cell 31
# **Replaying a specific point:** each snapshot carries its own `config` (with a `checkpoint_id`). Passing that config back into the graph resumes execution *from that exact checkpoint*, this is "time travel", you can inspect, or even fork a new branch of execution from, any earlier point in the run instead of only the latest state.

# %% [code] Cell 32
# Find the checkpoint captured right before the self-correction loop's second `generate` call.
target = next(
    (s for s in history if s.next == ("generate",) and s.values.get("retry_count", 0) == 1),
    None,
)

if target is None:
    print("No second-generate checkpoint exists.")
    print("The first critique accepted the draft, so the graph did not enter the self-correction loop.")
else:
    print("Replaying from checkpoint at step", target.metadata.get("step"))
    print("State at that point:")
    print(" ", target.values["draft"][:90], "...")
    print(" ", "critique_feedback:", target.values["critique_feedback"])

    replayed = full_graph.invoke(None, target.config)
    print("\nRe-running from that checkpoint:")
    print(" ", "__interrupt__" in replayed)

# %% [markdown] Cell 33
# ### `AgentExecutor` vs `LangGraph`: when to reach for each
# 
# | | `AgentExecutor` (Day 2) | `LangGraph` (Day 3) |
# |---|---|---|
# | **Control flow** | One fixed ReAct loop, internal to the executor | Explicit graph you design, linear, branching, or cyclical |
# | **State** | Implicit: chat history plus `agent_scratchpad` | Explicit, typed `State` object with per-key reducers |
# | **Multiple / nested loops** | Hard, you would hand-roll retry logic around the executor | Native, just add more conditional edges |
# | **Pausing for human input** | Not supported natively, you would break out of the loop yourself | Native, via `interrupt()` plus a checkpointer |
# | **Persistence / resuming** | Not built in | Native, via checkpointers (`MemorySaver`, SQLite, Postgres, and so on) |
# | **Debugging** | `verbose=True` shows Act/Observe, not the full trace | `get_state_history()` gives a full, replayable timeline |
# | **Setup cost** | Very low, a few lines to get a working tool-calling agent | Higher, you design nodes, edges, and state up front |
# 
# **Reach for `AgentExecutor`** (or better, the modern `create_agent`) when you need a single agent loop with tools and nothing more exotic: a quick prototype, a Q&A bot, a simple tool-calling assistant where "reason, act, observe, repeat" is the whole story.
# 
# **Reach for `LangGraph`** the moment the workflow has more than one distinct phase, needs a self-correction or multi-agent loop, must pause for a human before an irreversible action, or needs to survive a process restart mid-workflow (for example a long-running approval that a user might not respond to for hours). Task 3's self-correction loop and Task 4's approval gate are exactly the two signals that mean "this needs LangGraph, not a plain executor."
# 
# %% [code] Cell 34 - Interactive Research Assistant
# Interactive chat with the research assistant workflow
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔬 RESEARCH ASSISTANT AGENT")
    print("="*70)
    print("I can help you research topics by:")
    print("  • Planning a search strategy")
    print("  • Retrieving web documents")
    print("  • Generating and self-critiquing answers")
    print("  • Getting human approval before final reports")
    print("\n💡 Type your research question or 'quit' to exit")
    print("="*70 + "\n")
    
    session_counter = 1
    
    while True:
        topic = input("🔍 Your research question: ").strip()
        
        if topic.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye! Research complete.")
            break
            
        if not topic:
            continue
        
        # Create a new session for each question
        thread_id = f"chat-session-{session_counter}"
        config = {"configurable": {"thread_id": thread_id}}
        init_state = make_init_state(topic)
        
        print("\n" + "-"*70)
        print("🤖 Agent is researching...\n")
        
        try:
            # Run the graph until it hits the interrupt
            result = full_graph.invoke(init_state, config)
            
            # Check if we hit an interrupt (human approval needed)
            if "__interrupt__" in result:
                print("⏸️  Agent needs your approval before sending the final report.")
                print("\n📄 Draft preview:")
                print("-"*70)
                print(result.get("draft", "(No draft available)")[:500] + "...")
                print("-"*70)
                
                # Get user decision
                while True:
                    decision = input("\n✅ Approve sending this report? (yes/no): ").strip().lower()
                    if decision in ['yes', 'y']:
                        approved = True
                        break
                    elif decision in ['no', 'n']:
                        approved = False
                        break
                    else:
                        print("Please answer 'yes' or 'no'")
                
                # Resume with the decision
                resumed = full_graph.invoke(
                    Command(resume={"approved": approved}), 
                    config
                )
                
                print("\n" + "="*70)
                print("📊 FINAL RESULT")
                print("="*70)
                print(resumed["final_output"])
                
                # Show the reasoning log
                print("\n" + "-"*70)
                print("📋 RESEARCH PROCESS LOG:")
                print("-"*70)
                for line in resumed["log"]:
                    print(f"  {line}")
                print("="*70 + "\n")
                
            else:
                # No interrupt (shouldn't happen in our workflow, but just in case)
                print("="*70)
                print("📊 FINAL RESULT")
                print("="*70)
                print(result.get("final_output", "(No output)"))
                print("="*70 + "\n")
                
        except Exception as e:
            print(f"❌ Error: {e}\n")
            print("Please try a different question.\n")
            continue
        
        session_counter += 1