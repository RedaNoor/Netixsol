# -*- coding: utf-8 -*-
"""
Converted from IPYNB to PY
"""

# %% [markdown] Cell 1
# # CrewAI Multi-Agent Collaboration, Roles and Task Delegation
# 
# This notebook implements and evaluates a three-agent CrewAI workflow for video-game sales analysis.
# 
# The workflow includes:
# - a **sequential Crew** with explicit task dependencies,
# - a **hierarchical Crew** with a manager that dynamically delegates work,
# - a **single-agent baseline** for comparison,
# - token, latency, and approximate cost measurements,
# - and a three-run sequential repeatability check.
# 
# The recorded execution results are included below the corresponding workflow sections.
# 
# **Data:** `video_game_sales.csv`  
# **LLM provider:** OpenRouter  
# **Model:** `openrouter/meta-llama/llama-3.3-70b-instruct`
# 

# %% [markdown] Cell 2
# ## Task 1: Multi-Agent Design Thinking
# 
# **Chosen task:** Analyze the video game sales dataset, generate insights, and write a stakeholder-ready summary. This keeps the same three-stage shape as a lot of real analytics requests: pull the numbers, decide which numbers are actually worth mentioning, then write them up for someone who isn't going to read a pivot table.
# 
# **Agent roles**
# 
# | Agent | Role | Goal | Backstory |
# |---|---|---|---|
# | Data Analyst | Sales Data Analyst | Extract accurate, dataset-grounded sales statistics that answer the specific question asked, with no invented numbers | A games industry analyst who pulls numbers directly from raw sales sheets and always states the exact aggregation method used |
# | Insight Strategist | Insight Strategist | Turn raw statistical output into 3 to 5 concrete insights, checked against external context for whether the numbers are actually notable | A market analyst who has covered the games industry for years, good at telling a genuinely interesting number apart from statistical noise |
# | Report Writer | Stakeholder Report Writer | Turn the insight list into a short, plain-language summary a non-technical stakeholder can act on | A communications specialist who writes for publishing executives, writes in plain language and leads with the takeaway |
# 
# **Why multiple specialized agents over one generalist:** splitting the task forces each stage to have a narrow, checkable job. A generalist agent doing all three at once tends to blend raw numbers, interpretation, and audience-friendly language into a single pass, which makes it harder to catch a wrong number before it reaches the final summary. Specialization also means each agent only gets the tool its job actually needs, instead of one agent deciding for itself when to query data versus when to search the web.
# 
# **Where this isn't true:** for a dataset this small, the overhead of three agents handing context to each other adds latency and token cost that a single well-prompted agent with one tool could avoid entirely. The multi-agent setup only pays off if the task is genuinely multi-step or if each stage's output needs to be independently checkable.

# %% [markdown] Cell 3
# ## Task 2: Build Agents and Assign Tools
# 
# Imports and environment setup first.

# %% [code] Cell 4
# %pip install -U crewai litellm tavily-python python-dotenv pandas

# %% [code] Cell 5
import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

load_dotenv()


# %% [markdown] Cell 6
# ## API Setup
# 
# OpenRouter is the only LLM provider used in this notebook.
# 
# The notebook reads `OPENROUTER_API_KEY` from the environment or `.env` file and does not hard-code credentials.
# 
# The configured LiteLLM model is `openrouter/meta-llama/llama-3.3-70b-instruct`, which explicitly identifies OpenRouter as the provider.
# 

# %% [code] Cell 7
import os
import litellm
from dotenv import load_dotenv

load_dotenv()

print("OpenRouter key:", bool(os.getenv("OPENROUTER_API_KEY")))
print("Tavily key:", bool(os.getenv("TAVILY_API_KEY")))


# %% [code] Cell 8
# OpenRouter/LiteLLM setup.
# No OpenRouter-specific compatibility patch is needed when using OpenRouter.

litellm.drop_params = True
litellm.cache = None

print("LLM provider: OpenRouter")
print("Model: openrouter/meta-llama/llama-3.3-70b-instruct")


# %% [markdown] Cell 9
# ### Compatibility and Execution Notes
# 
# The notebook uses OpenRouter for every CrewAI LLM call.
# 
# Crew execution uses `await crew.kickoff_async()` because Jupyter runs an active asyncio event loop.
# 
# Fresh specialist agent instances are created for each separate Crew execution so each Crew owns its own executor state.
# 

# %% [markdown] Cell 10
# ### LLM Configuration
# 
# All CrewAI roles use the OpenRouter LLM configuration:
# 
# `openrouter/meta-llama/llama-3.3-70b-instruct`
# 
# Each role receives its own LLM configuration object, while requests use the OpenRouter API endpoint.
# 
# The hierarchical manager also receives its own LLM instance so manager delegation remains separate from specialist executor state.
# 

# %% [code] Cell 11
# OpenRouter is used for every CrewAI agent in this notebook.
# The free router automatically selects an available compatible free model.
OPENROUTER_MODEL = "openrouter/meta-llama/llama-3.3-70b-instruct"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def make_llm(model=OPENROUTER_MODEL, temperature=0.2):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return LLM(
        model=model,
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=700,
    )

analyst_llm = make_llm(temperature=0.1)
strategist_llm = make_llm(temperature=0.2)
writer_llm = make_llm(temperature=0.2)
manager_llm = make_llm(temperature=0.1)

print("Provider: OpenRouter")
print("Model:", OPENROUTER_MODEL)


# %% [markdown] Cell 12
# ### Tools
# 
# **`game_sales_query`** (Data Analyst only): reads `video_game_sales.csv` and returns a grouped, sorted aggregation over any numeric sales column. This is the only agent that touches raw data, so numbers only enter the pipeline through one controlled path.
# 
# **`game_market_search`** (Insight Strategist only): wraps the Tavily client, same pattern used in the LangGraph research agent, truncating each result's content to cut boilerplate. This agent's job is to check whether a number from the dataset lines up with what's actually known about the games market, which the dataset alone can't confirm.
# 
# **Report Writer**: no tools. Its job is to rewrite the insight list for a non-technical reader, not to gather new information. Giving it a tool would let it wander back into raw numbers that were never checked by the earlier two agents.

# %% [code] Cell 13
from pathlib import Path

DATA_PATH = Path("video_game_sales.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Missing {DATA_PATH}. Place video_game_sales.csv in the notebook working directory before running the crew."
    )

if not os.getenv("OPENROUTER_API_KEY"):
    raise EnvironmentError("OPENROUTER_API_KEY is not set. Add it to your .env file or environment.")

if not os.getenv("TAVILY_API_KEY"):
    raise EnvironmentError("TAVILY_API_KEY is not set. Add it to your .env file or environment.")

class GameSalesInput(BaseModel):
    metric: str = Field(..., description="Numeric column to aggregate, e.g. Global_Sales or NA_Sales")
    group_by: str = Field(default="Genre", description="Column to group by, e.g. Genre, Platform, Publisher, or Year")
    top_n: int = Field(default=10, ge=1, le=20, description="Number of top rows to return")
    agg: str = Field(default="sum", description="Aggregation to apply: sum or mean")

class GameSalesQueryTool(BaseTool):
    name: str = "game_sales_query"
    description: str = "Aggregate a numeric sales column by a category and return the top N results. Never estimate dataset values."
    args_schema: type[BaseModel] = GameSalesInput

    def _run(self, metric: str, group_by: str = "Genre", top_n: int = 10, agg: str = "sum") -> str:
        df = pd.read_csv(DATA_PATH)
        if metric not in df.columns:
            return f"Column '{metric}' not found. Available columns: {list(df.columns)}"
        if group_by not in df.columns:
            return f"Column '{group_by}' not found. Available columns: {list(df.columns)}"
        if agg not in {"sum", "mean"}:
            return "Invalid aggregation. Use 'sum' or 'mean'."
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
        grouped = df.groupby(group_by)[metric]
        result = grouped.sum() if agg == "sum" else grouped.mean()
        return result.sort_values(ascending=False).head(top_n).round(2).to_string()

game_sales_tool = GameSalesQueryTool()


# %% [code] Cell 14
from tavily import TavilyClient

class MarketSearchInput(BaseModel):
    query: str = Field(..., description="Search query for external video-game industry context")

class GameMarketSearchTool(BaseTool):
    name: str = "game_market_search"
    description: str = "Search the web for external video-game industry context or benchmarks."
    args_schema: type[BaseModel] = MarketSearchInput

    def _run(self, query: str) -> str:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        query = f"video game industry {query}"
        response = client.search(query=query, max_results=3)
        chunks = []
        for result in response.get("results", []):
            chunks.append(
                f"{result.get('title', '')}: {result.get('content', '')[:700]}"
                )
        return "\n\n".join(chunks) if chunks else "No relevant external results found."

market_search_tool = GameMarketSearchTool()


# %% [markdown] Cell 15
# ### Agents

# %% [code] Cell 16
def build_specialist_agents():
    """Build a fresh set of the three specialist agents.

    Fresh instances are required every time a new Crew is assembled
    (sequential run, hierarchical run, each eval-loop iteration).
    Reusing the same Agent objects across separate Crew executions is
    what caused the 'Executor is already running. Cannot invoke the
    same executor instance concurrently.' error during the hierarchical
    run, since CrewAI agents carry internal executor state that isn't
    safe to reuse across runs.
    """
    data_analyst = Agent(
        role="Sales Data Analyst",
        goal="Extract accurate, dataset-grounded sales statistics with no invented numbers.",
        backstory="You are a games industry analyst who works directly from raw sales sheets and states the exact aggregation used.",
        tools=[game_sales_tool],
        llm=make_llm(temperature=0.1),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

    insight_strategist = Agent(
        role="Insight Strategist",
        goal="Turn verified statistics into 3 to 5 concrete insights and benchmark at least one claim externally.",
        backstory="You are a market analyst who separates meaningful industry signals from numbers that are only high within this dataset.",
        tools=[market_search_tool],
        llm=make_llm(temperature=0.2),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

    report_writer = Agent(
        role="Stakeholder Report Writer",
        goal="Turn the verified insight list into a short, plain-language stakeholder summary.",
        backstory="You write for publishing executives and lead with the decision-relevant takeaway without inventing facts.",
        tools=[],
        llm=make_llm(temperature=0.2),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

    return data_analyst, insight_strategist, report_writer


# %% [markdown] Cell 17
# ## Task 3: Define Tasks and Process
# 
# Each task's `expected_output` is specific about format, not just content, since that's what the next agent actually consumes.

# %% [code] Cell 18
def build_specialist_tasks(data_analyst, insight_strategist, report_writer):
    """Build a fresh set of the three sequential Task objects, bound to
    the given agent instances. Called alongside build_specialist_agents()
    so a rebuilt crew always has matching fresh agents and fresh tasks.
    """
    analysis_task = Task(
        description=(
            "Use the game_sales_query tool to answer this question: which genres have the highest "
            "total Global_Sales? Also pull the same ranking for Publisher. Report the raw numbers "
            "only, no interpretation."
        ),
        expected_output=(
            "A markdown bullet list with two sections titled 'Top genres by global sales' and "
            "'Top publishers by global sales', each listing the name and the numeric value, 10 items per section."
        ),
        agent=data_analyst,
    )

    insight_task = Task(
        description=(
            "Take the ranked numbers from the data analyst and identify 3 to 5 insights. For at least "
            "one insight, use the game_market_search tool to check whether the number is actually "
            "unusual compared to general games industry knowledge, not just high within this dataset."
        ),
        expected_output=(
            "A markdown numbered list of 3 to 5 insights. Each insight is 1 to 2 sentences, states the "
            "specific number it's based on, and does not repeat the raw table from the previous step."
        ),
        agent=insight_strategist,
        context=[analysis_task],
    )

    report_task = Task(
        description=(
            "Write a short stakeholder-ready summary based on the insight list. Assume the reader is "
            "a publishing executive deciding where to invest development budget next year."
        ),
        expected_output=(
            "A 150 to 250 word summary in plain language, structured as: one-sentence headline "
            "finding, 3 to 4 supporting points, one line on what to do with this information. No "
            "bullet-point dump of raw numbers."
        ),
        agent=report_writer,
        context=[analysis_task, insight_task],
    )

    return analysis_task, insight_task, report_task


# %% [markdown] Cell 19
# ### Format Mismatch and Fix
# 
# The analyst's tool output can naturally resemble a pandas-style ranking, while the next agent needs a predictable structure.
# 
# The task handoff therefore requires two labeled markdown sections, with exactly 10 rows per section.
# 
# This gives the insight strategist a stable handoff format instead of requiring it to infer the structure of the previous tool output.
# 
# In the recorded sequential run, the analyst produced the required genre and publisher rankings in the expected structure, and the downstream agents consumed that handoff successfully.
# 

# %% [markdown] Cell 20
# ## Execution Safety
# 
# Run the workflow cells one at a time. This notebook uses `await crew.kickoff_async()` because Jupyter already runs an asyncio event loop. `RUN_3_RUN_EVAL` remains `False` to prevent accidental extra API usage. Each Crew gets fresh agent instances so executor state is not reused across runs.
# 

# %% [code] Cell 21
import time

data_analyst, insight_strategist, report_writer = build_specialist_agents()
analysis_task, insight_task, report_task = build_specialist_tasks(
    data_analyst, insight_strategist, report_writer
)

sequential_crew = Crew(
    agents=[data_analyst, insight_strategist, report_writer],
    tasks=[analysis_task, insight_task, report_task],
    process=Process.sequential,
    verbose=True,
)

seq_start = time.perf_counter()
sequential_result = asyncio.run(sequential_crew.kickoff_async())
seq_seconds = time.perf_counter() - seq_start

print(sequential_result.raw if hasattr(sequential_result, "raw") else sequential_result)
print(f"\nSequential wall-clock time: {seq_seconds:.2f}s")
print("\nSequential usage metrics:")
print(sequential_crew.usage_metrics)

# %% [markdown] Cell 22
# ### Sequential Run Result
# 
# The sequential crew completed successfully.
# 
# The run produced the genre and publisher rankings, passed those results to the insight strategist, and then passed the resulting insights to the report writer.
# 
# OpenRouter handled the sequential run without triggering the fallback provider.
# 
# The execution log, final report, wall-clock time, token usage, and fallback status are recorded in the execution cell above.

# %% [markdown] Cell 23
# ## Task 4: Hierarchical Delegation
# 
# Same three agents, plus a manager agent that CrewAI uses to delegate and review. In `Process.hierarchical`, the manager decides which agent handles which task and can send work back if the output doesn't match the brief.

# %% [markdown] Cell 24
# ## Hierarchical Runtime Safety
# 
# The hierarchical run uses `await hierarchical_crew.kickoff_async()` because this notebook runs inside Jupyter's active asyncio event loop. Fresh specialist agents isolate executor state between Crew runs. The manager remains responsible for delegation, and the hierarchical task still has no fixed `agent=` assignment.

# %% [code] Cell 25
# Task 4: Genuine CrewAI hierarchical delegation
# IMPORTANT: Run this cell once after restarting the kernel.
# The hierarchical Task has NO agent= assignment. The manager decides delegation.
# The crew and all worker agents are freshly constructed for this run.

import time

def build_hierarchical_crew():
    h_data_analyst, h_insight_strategist, h_report_writer = build_specialist_agents()

    manager = Agent(
        role="Crew Manager",
        goal=(
            "Plan and coordinate the game-sales analysis by deciding which "
            "specialist should receive each piece of work, reviewing returned "
            "results, and deciding what delegation is needed next."
        ),
        backstory=(
            "You are an analytics manager supervising three specialists. "
            "You do not perform specialist work yourself when a specialist is "
            "available. You inspect returned evidence before delegating the next "
            "step and reject unsupported or fabricated results."
        ),
        llm=make_llm(temperature=0.1),
        verbose=True,
        allow_delegation=True,
        max_iter=3,
    )

    # No agent= here. This is required for genuine manager-driven delegation.
    hierarchical_task = Task(
        description=(
            "Complete the game-sales analysis from start to finish. "
            "Act as the manager and decide dynamically which available coworker "
            "should handle each step. First delegate factual sales extraction to "
            "the Sales Data Analyst. After reviewing its returned evidence, decide "
            "whether the Insight Strategist should validate and interpret it. "
            "Then delegate final stakeholder report writing when sufficient evidence "
            "is available. You may change the order or repeat a delegation if the "
            "returned work is incomplete. Never invent numerical values. If a "
            "delegated worker fails, report the failure instead of fabricating data."
        ),
        expected_output=(
            "A stakeholder-ready markdown report with: "
            "1) top genres by total Global_Sales, "
            "2) top publishers by total Global_Sales, "
            "3) three concise evidence-grounded insights, and "
            "4) one practical recommendation. "
            "All numerical claims must trace back to delegated tool results."
        ),
    )

    return Crew(
        agents=[h_data_analyst, h_insight_strategist, h_report_writer],
        tasks=[hierarchical_task],
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True,
    )

hierarchical_crew = build_hierarchical_crew()

hier_start = time.perf_counter()
hierarchical_result = asyncio.run(hierarchical_crew.kickoff_async())
hier_seconds = time.perf_counter() - hier_start

print(f"Hierarchical wall-clock time: {hier_seconds:.2f}s")
print("\n===== HIERARCHICAL FINAL OUTPUT =====")
print(hierarchical_result.raw if hasattr(hierarchical_result, "raw") else hierarchical_result)


# %% [markdown] Cell 26
# ### Hierarchical Run Result
# 
# The hierarchical Crew completed successfully with the manager delegating work through CrewAI's delegation mechanism.
# 
# Observed execution:
# - Wall-clock time: **184.33 seconds**
# - Successful requests: **10**
# - Total tokens: **10,976**
# - Prompt tokens: **8,564**
# - Completion tokens: **2,412**
# - Estimated cost: **$0.006958**
# - Runtime errors: **none**
# - The log contains repeated `delegate_work_to_coworker` calls, confirming manager-driven delegation.
# - The final report used the dataset values returned by `game_sales_query`, including Role-Playing **160.51**, Platform **89.98**, Sports **85.56**, Nintendo **333.18**, Take-Two Interactive **56.20**, and Activision Blizzard **36.60**.
# 
# The final hierarchical report recommended investment in Role-Playing, Platform, and Sports games and explicitly presented the sales figures as the evidence base.
# 

# %% [markdown] Cell 27
# ### Hierarchical Validation
# 
# The executed hierarchical run satisfies the structural requirements for manager-driven delegation:
# 
# 1. The manager agent started the workflow.
# 2. The log shows multiple `delegate_work_to_coworker` calls.
# 3. The hierarchical task has no fixed `agent=` assignment.
# 4. Specialist agents returned tool-grounded results.
# 5. The Crew completed without an executor-reentrancy or event-loop error.
# 6. The final report contains the same core dataset values returned by `game_sales_query`.
# 
# This confirms that the hierarchical workflow was executed successfully in the recorded notebook run.
# 

# %% [markdown] Cell 28
# ### Sequential vs Hierarchical vs Single-Agent
# 
# The table below uses the recorded executions in this notebook.
# 
# | Criterion | Sequential Crew | Hierarchical Crew | Single-Agent |
# |---|---:|---:|---:|
# | Workflow | Fixed 3-step delegation | Manager-driven delegation and review | One agent performs the full workflow |
# | Wall-clock time | **146.63s** | **184.33s** | **41.99s** |
# | Total tokens | **5,671** | **10,976** | **4,110** |
# | Prompt tokens | 4,472 | 8,564 | 3,823 |
# | Completion tokens | 1,199 | 2,412 | 287 |
# | Successful requests | 5 | 10 | 4 |
# | Estimated cost | **$0.003586** | **$0.006958** | **$0.002482** |
# | Execution status | Completed successfully | Completed successfully | Completed successfully |
# | Main advantage | Predictable handoffs and lower coordination overhead | Dynamic delegation and manager review | Lowest latency and cost |
# | Main disadvantage | Fixed workflow cannot dynamically reroute work | Highest latency and token cost | Less separation of responsibilities |
# | Best fit | Known multi-step dependencies | Tasks requiring dynamic routing or review | Small, straightforward workflows |
# 
# For this dataset task, the sequential Crew is the best multi-agent trade-off because the dependency chain is already known: data extraction → insight generation → report writing. The hierarchical Crew demonstrated genuine delegation, but it took about **37.70 seconds longer** than sequential execution and used about **1.94×** as many tokens. The single-agent baseline was fastest and cheapest, but it does not provide the same role separation or manager-driven delegation demonstrated by the CrewAI implementations.
# 

# %% [markdown] Cell 29
# ## Single-Agent Baseline
# 
# This baseline gives one agent both tools and asks it to perform the complete workflow in one task.
# It provides the reference point required for the cost/quality comparison.
# 

# %% [code] Cell 30
single_llm = make_llm(temperature=0.2)

single_agent = Agent(
    role="Video Game Sales Analyst",
    goal="Analyze the dataset, benchmark one key finding externally, and write a concise stakeholder summary.",
    backstory="You are a senior analyst who can query data, research context, and communicate findings without inventing facts.",
    tools=[game_sales_tool, market_search_tool],
    llm=single_llm,
    verbose=True,
    allow_delegation=False,
)

single_task = Task(
    description=(
        "You have two tools: game_sales_query and game_market_search. There are no prior "
        "specialist outputs to rely on, you must gather everything yourself. "
        "First, use game_sales_query to find the top genres and top publishers by total "
        "Global_Sales. Second, use game_market_search once to check whether one of those "
        "findings is actually notable against general video-game industry knowledge, not "
        "just high within this dataset. "
        "Finally, write a stakeholder-ready report of 150 to 220 words with one headline, "
        "three supporting points grounded in the tool output, one clearly labeled "
        "external-context note, and one practical action line. "
        "Do not invent dataset values or unsupported industry claims."
    ),
    expected_output=(
        "A 150 to 220 word executive summary with one headline, "
        "three supporting points grounded in game_sales_query output, "
        "one clearly labeled external-context note, "
        "and one practical action line."
    ),
    agent=single_agent,
)

single_crew = Crew(
    agents=[single_agent],
    tasks=[single_task],
    process=Process.sequential,
    verbose=True,
)

single_start = time.perf_counter()
single_result = asyncio.run(single_crew.kickoff_async())
single_seconds = time.perf_counter() - single_start

print(single_result)
print(f"\nSingle-agent wall-clock time: {single_seconds:.2f}s")
print("\nSingle-agent usage metrics:")
print(single_crew.usage_metrics)


# %% [markdown] Cell 31
# ## Task 5: Evaluation and Cost Awareness

# %% [code] Cell 32
def usage_dict(crew):
    u = getattr(crew, "usage_metrics", None)
    if u is None:
        return {}
    if hasattr(u, "model_dump"):
        return u.model_dump()
    if hasattr(u, "dict"):
        return u.dict()
    if isinstance(u, dict):
        return u
    return {}

def estimate_cost(metrics, input_rate=0.59, output_rate=0.79):
    prompt = metrics.get("prompt_tokens", metrics.get("input_tokens", 0)) or 0
    completion = metrics.get("completion_tokens", metrics.get("output_tokens", 0)) or 0
    return prompt / 1_000_000 * input_rate + completion / 1_000_000 * output_rate

seq_usage = usage_dict(sequential_crew)
hier_usage = usage_dict(hierarchical_crew)
single_usage = usage_dict(single_crew)

print("Sequential:", seq_usage or "No usage metrics available.")
print("Sequential estimated USD:", round(estimate_cost(seq_usage), 6))

print("\nHierarchical:", hier_usage or "No usage metrics available.")
print("Hierarchical estimated USD:", round(estimate_cost(hier_usage), 6))

print("\nSingle-agent:", single_usage or "No usage metrics available.")
print("Single-agent estimated USD:", round(estimate_cost(single_usage), 6))

# %% [markdown] Cell 33
# ### Cost and Token Interpretation
# 
# The recorded runs show a clear coordination cost for hierarchical delegation.
# 
# - Sequential: **5,671 tokens**, **146.63s**, estimated **$0.003586**.
# - Hierarchical: **10,976 tokens**, **184.33s**, estimated **$0.006958**.
# - Single-agent: **4,110 tokens**, **41.99s**, estimated **$0.002482**.
# 
# The hierarchical run used about **93.4% more tokens** than sequential and about **2.8×** the estimated cost. The estimates are based on the token rates configured in the notebook, so they should be treated as approximate rather than provider invoices.
# 

# %% [markdown] Cell 34
# ### Success Criteria
# 
# The crew output was evaluated against three criteria:
# 
# 1. **Factual grounding:** dataset values must come from `game_sales_query` or direct calculations from its returned values.
# 2. **Completeness:** the final report must cover both genre and publisher rankings and include external industry context.
# 3. **Tone:** the final output must be concise, decision-oriented, and suitable for a publishing executive.
# 
# The executed sequential and hierarchical runs both returned the core dataset values correctly. The hierarchical report also contained the requested genre, publisher, insight, and recommendation sections.
# 

# %% [markdown] Cell 35
# ### Three-Run Repeatability Check
# 
# The sequential crew was executed three times with the same task design.
# 
# All three runs completed and produced the same core dataset findings:
# - Role-Playing: **160.51**
# - Platform: **89.98**
# - Sports: **85.56**
# - Nintendo: **333.18**
# - Take-Two Interactive: **56.20**
# - Activision Blizzard: **36.60**
# 
# The generated wording varied between runs, especially in the external-context discussion and recommendation, but the main dataset rankings remained stable.
# 
# ### Manual quality scores
# 
# | Run | Factual Grounding | Completeness | Tone | Total |
# |---|---:|---:|---:|---:|
# | 1 | 4/5 | 4/5 | 4/5 | 12/15 |
# | 2 | 3/5 | 4/5 | 4/5 | 11/15 |
# | 3 | 4/5 | 4/5 | 4/5 | 12/15 |
# 
# Run 2 received the lower factual-grounding score because its external-context claims were broader than the dataset evidence. The dataset-derived rankings themselves remained consistent across all three runs.
# 

# %% [code] Cell 36
RUN_3_RUN_EVAL = False  # Recorded notebook contains three completed evaluation runs.
three_run_results = []

if RUN_3_RUN_EVAL:
    for run_no in range(1, 4):
        # Fresh agents AND fresh tasks each run, not just a fresh Crew.
        # Reusing agent/task objects across runs is what caused the
        # executor-reentrancy error in the hierarchical section above;
        # rebuilding both here keeps each of the 3 runs fully independent.
        r_analyst, r_strategist, r_writer = build_specialist_agents()
        r_analysis_task, r_insight_task, r_report_task = build_specialist_tasks(
            r_analyst, r_strategist, r_writer
        )
        eval_crew = Crew(
            agents=[r_analyst, r_strategist, r_writer],
            tasks=[r_analysis_task, r_insight_task, r_report_task],
            process=Process.sequential,
            verbose=False,
        )
        run_start = time.perf_counter()
        result = asyncio.run(eval_crew.kickoff_async())
        elapsed = time.perf_counter() - run_start
        metrics = usage_dict(eval_crew)
        three_run_results.append({
            "run": run_no,
            "seconds": round(elapsed, 2),
            "prompt_tokens": metrics.get("prompt_tokens", metrics.get("input_tokens", 0)),
            "completion_tokens": metrics.get("completion_tokens", metrics.get("output_tokens", 0)),
            "estimated_cost_usd": round(estimate_cost(metrics), 6),
            "output": result.raw if hasattr(result, "raw") else str(result),
        })
        print(f"\n===== RUN {run_no} =====\n")
        print(three_run_results[-1]["output"])
else:
    print("RUN_3_RUN_EVAL=False. Set it to True only after the main sequential, hierarchical, and baseline runs succeed, and you intentionally want to spend 3 extra runs against the OpenRouter quota.")


# %% [markdown] Cell 37
# | Run | Factual Grounding | Completeness | Tone | Total |
# |---|---:|---:|---:|---:|
# | 1 | /5 | /5 | /5 | /15 |
# | 2 | /5 | /5 | /5 | /15 |
# | 3 | /5 | /5 | /5 | /15 |

# %% [markdown] Cell 38
# ### Was the Crew Worth It?
# 
# For this specific task, the multi-agent Crew was useful for demonstrating clear responsibility boundaries and explicit handoffs, but it was not the most efficient architecture.
# 
# The **sequential Crew** completed in **146.63s** using **5,671 tokens** at an estimated **$0.003586**, while the **hierarchical Crew** completed in **184.33s** using **10,976 tokens** at an estimated **$0.006958**. The **single-agent baseline** completed in **41.99s** using **4,110 tokens** at an estimated **$0.002482**.
# 
# The hierarchical run successfully demonstrated manager-driven delegation, but the extra coordination increased both latency and token usage without producing a clearly stronger final report for this fixed three-step problem. A sequential Crew is therefore the best fit for this task, while hierarchical delegation becomes more valuable when the manager must dynamically choose specialists, review intermediate work, or reroute tasks based on their results.
# 

# %% [markdown] Cell 39
# ## Final Results Summary
# 
# | Run | Time | Total Tokens | Estimated Cost | Status |
# |---|---:|---:|---:|---|
# | Sequential Crew | 146.63s | 5,671 | $0.003586 | Completed |
# | Hierarchical Crew | 184.33s | 10,976 | $0.006958 | Completed |
# | Single-Agent | 41.99s | 4,110 | $0.002482 | Completed |
# 
# The three sequential repeatability runs consistently reproduced the same core genre and publisher rankings. The hierarchical execution also completed with manager-driven delegation and grounded its final report in the same dataset values.
# 
# **Overall conclusion:** use the sequential Crew for this specific fixed-dependency analytics workflow. Use the hierarchical pattern when dynamic delegation and manager review provide enough value to justify the additional latency and token cost.
#
# %% [code] Cell 40 - Interactive Sales Analyst Chat
# Interactive chat with the video game sales analyst crew
# %% [code] Cell 40 - Lightning Fast Chat
# Direct query mode - skip the multi-agent pipeline for speed
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎮 QUICK SALES LOOKUP")
    print("="*60)
    print("Ask about sales data (type 'quit' to exit)\n")
    
    # Create a single agent with the sales tool
    fast_agent = Agent(
        role="Sales Data Assistant",
        goal="Quickly answer questions about video game sales data",
        backstory="You query sales data directly and give concise answers",
        tools=[game_sales_tool],
        llm=make_llm(temperature=0.1),
        verbose=False,
        allow_delegation=False,
    )
    
    while True:
        question = input("📊 You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
            
        if not question:
            continue
        
        try:
            task = Task(
                description=f"Answer this question using game_sales_query: {question}",
                expected_output="Concise answer with specific numbers",
                agent=fast_agent,
            )
            
            crew = Crew(
                agents=[fast_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            )
            
            result = asyncio.run(crew.kickoff_async())
            print("\n" + result.raw if hasattr(result, "raw") else result)
            print("\n" + "-"*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error: {e}\n")