# -*- coding: utf-8 -*-
"""
Converted from IPYNB to PY
"""

# %% [markdown] Cell 1
# # LangChain Agent: Tools, Chains, Memory and Structured Output
# 
# This notebook rebuilds the raw-Python ReAct agent from the previous task using LangChain, then extends it with LCEL chains, conversation memory, external data access, structured output, and basic tool error handling.
# 
# The notebook uses Groq as the LLM provider through LangChain. Anthropic is not required for this implementation.
# 
# The deterministic tool functions were tested independently against the local calculator logic, weather data, and game dataset. The LLM-dependent agent workflows were also executed successfully with the configured Groq model, including the memory workflow and final structured-output integration test.
# 
# The final integration test verifies a three-turn conversation using the same session history, tool calls against the game dataset and calculator, and extraction of the final recommendation into the `GameRecommendation` Pydantic model.
# 
# The notebook also includes an error-handling demonstration for an unreliable storefront tool and an annotated execution trace showing the observable action → observation → final-answer flow.
# 

# %% [markdown] Cell 2
# ## Task 1: LangChain Setup and Core Concepts
# 
# ### Concept Mapping: Raw Python → LangChain
# 
# | Raw-Python agent component                                        | LangChain equivalent                                                                        |
# | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
# | `while True` loop calling the LLM and checking for tool calls     | `AgentExecutor`, which manages the agent/tool execution loop                                |
# | `if tool_name == "calculator": ...` dispatch logic                | `@tool`-decorated functions registered with the agent                                       |
# | Manually appending assistant and tool messages to a list          | `RunnableWithMessageHistory` with a message-history store                                   |
# | `system_prompt` defining the agent's behavior                     | `ChatPromptTemplate` with system instructions and `MessagesPlaceholder("agent_scratchpad")` |
# | `response.model` logging after each LLM call                      | Still requires custom logging or callbacks in LangChain                                     |
# | Regex validation, `strip_emojis()`, and other normal Python logic | Unchanged Python functions that can be wrapped as LangChain tools                           |
# 
# ### LLM Provider  
# This implementation uses Groq through LangChain's `ChatGroq` integration. OpenRouter is kept as a commented-out alternative so the model provider can be changed without changing the rest of the agent architecture. Anthropic is not required for this implementation.
# 

# %% [code] Cell 3
#%pip install -U langchain langchain-community langchain-groq langchain-classic python-dotenv
# %pip install langchain-openai  # (magic command commented out)

# %% [code] Cell 4
import os
import re
import json
import random
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from langchain_core.tools import tool, ToolException
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel, Field

# # --- Primary: Groq ---
# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     api_key=os.getenv("GROQ_API_KEY"),
#     temperature=0,
# )

#-- Fallback: OpenRouter (commented out, swap in if Groq rate-limits) ---
llm = ChatOpenAI(
    model="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)


# %% [markdown] Cell 5
# ### Basic LCEL Chain
# 
# A minimal LCEL pipeline that connects a prompt template, the LLM, and a string output parser. It demonstrates the basic `prompt → LLM → parser` flow before tools, agents, and memory are introduced.
# 
# The LCEL `|` operator composes these runnable components into a sequence. When the chain is invoked, the output from each component becomes the input to the next component.
# 

# %% [code] Cell 6
basic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant. Answer in one sentence."),
    ("human", "{question}")
])
basic_chain = basic_prompt | llm | StrOutputParser()
result = basic_chain.invoke({
    "question": "What does ReAct stand for in the context of LLM agents?"
})
print(result)

# %% [markdown] Cell 7
# ### What `|` Is Doing
# 
# The LCEL `|` operator composes LangChain `Runnable` components into a `RunnableSequence`, so the output of one component becomes the input to the next. For example, `basic_prompt | llm | StrOutputParser()` builds a reusable pipeline where the prompt is formatted, sent to the LLM, and converted to a string only when `.invoke()` is called. This is similar to manually calling `build_prompt()`, `call_llm()`, and extracting the response in the raw-Python agent, but LCEL represents the sequence as one composable chain.
# 

# %% [markdown] Cell 8
# ## Task 2: Define and Register Tools
# 
# The agent uses three tools. `calculator` and `get_weather` are reused from the raw-Python agent, while `lookup_game` is a new tool that reads game information from a local JSON database. The game lookup returns the developer, release year, genre, platforms, and average completion time, and supports exact and unambiguous partial title matches.
# 
# ### Tool Docstrings
# 
# The `@tool` decorator uses a function's docstring as the tool description that is included in the model-facing tool schema, together with the function name and argument information inferred from the signature. This means the docstring is part of the agent's tool-selection context, not just developer documentation. A useful docstring should explain what the tool does, what its input represents, and when the agent should use it, because vague descriptions can make tool selection less reliable.

# %% [code] Cell 9
SAFE_EXPR = re.compile(r'^[\d\s.+\-*/()%]+$')

@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression using numbers and +, -, *, /, %, and parentheses.
    Use this when the user asks for a numeric calculation, price comparison, or total.
    Does not support variables, functions, or non-arithmetic input.
    """
    expression = expression.strip()
    if not SAFE_EXPR.match(expression):
        return "Error: expression contains disallowed characters."
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Error: could not evaluate expression ({e})."


PK_WEATHER = {
    "karachi": {"condition": "Humid", "temp_c": 34},
    "lahore": {"condition": "Sunny", "temp_c": 38},
    "islamabad": {"condition": "Partly cloudy", "temp_c": 31},
    "peshawar": {"condition": "Hot", "temp_c": 37},
    "quetta": {"condition": "Clear", "temp_c": 27},
    "multan": {"condition": "Hot", "temp_c": 40},
    "faisalabad": {"condition": "Sunny", "temp_c": 36},
}

@tool
def get_weather(city: str) -> str:
    """Get weather data for a supported Pakistani city.
    Use this when the user asks about the weather in Karachi, Lahore, Islamabad, Peshawar, Quetta, Multan, or Faisalabad.
    Returns an error message for unsupported cities instead of guessing.
    """
    key = city.strip().lower()
    if key not in PK_WEATHER:
        return f"No weather data available for '{city}'. Covered cities: {', '.join(c.title() for c in PK_WEATHER)}."
    data = PK_WEATHER[key]
    return f"{city.title()}: {data['condition']}, {data['temp_c']}°C"


with open("data/games.json") as f:
    _GAMES = {g["title"].lower(): g for g in json.load(f)}

@tool
def lookup_game(title: str) -> str:
    """Look up a video game by title from the local JSON database.
    Returns the developer, release year, genre, platforms, and average completion time.
    Supports exact and unambiguous partial title matches and asks for a more specific title when multiple matches exist.
    """
    key = title.strip().lower()
    game = _GAMES.get(key)

    if game is None:
        matches = [g for k, g in _GAMES.items() if key in k]
        if len(matches) == 1:
            game = matches[0]
        elif len(matches) > 1:
            return f"Multiple matches for '{title}': {', '.join(g['title'] for g in matches)}. Be more specific."
        else:
            return f"No game found matching '{title}'."

    return (
        f"{game['title']} ({game['release_year']}): {game['genre']} game by "
        f"{game['developer']}, available on {game['platform']}. "
        f"Avg completion time: {game['avg_completion_hours']} hours."
    )

tools = [calculator, get_weather, lookup_game]

# %% [markdown] Cell 10
# ### Verifying the Tools Directly
# 
# Before giving the tools to the agent, each LangChain tool is tested directly with `.invoke()`. This isolates tool-level problems from agent behavior, so calculation, validation, weather lookup, and game-database errors can be identified before they are hidden inside an agent execution trace.
# 

# %% [code] Cell 11
print(calculator.invoke({"expression": "142 * 3 + 18"}))
print(calculator.invoke({"expression": "100 / 0"}))
print(calculator.invoke({"expression": "__import__('os').system('echo hacked')"}))

print()

print(get_weather.invoke({"city": "Lahore"}))
print(get_weather.invoke({"city": "Multan"}))
print(get_weather.invoke({"city": "Karachi Beach"}))

print()

print(lookup_game.invoke({"title": "PUBG"}))
print(lookup_game.invoke({"title": "Portal 2"}))
print(lookup_game.invoke({"title": "Hades"}))
print(lookup_game.invoke({"title": "Not A Real Game"}))

# %% [markdown] Cell 12
# The three tools were verified independently before being passed to the agent. The calculator returned the expected arithmetic result, handled division by zero, and rejected the attempted `__import__` expression through its input whitelist. The weather tool returned data for supported cities and returned a clear error for an unsupported location. The game lookup successfully returned records for PUBG, Portal 2, and Hades and returned a not-found message for an unknown title.
# 

# %% [markdown] Cell 13
# ## Task 3: Agent with `create_tool_calling_agent` / `AgentExecutor`
# 
# The agent combines the three registered tools with a prompt that tells the model when tool use is required. `create_tool_calling_agent` connects the model, tools, and agent prompt, while `AgentExecutor` manages the tool-calling execution loop and passes tool observations back to the model. `verbose=True` exposes the observable tool-call trace for debugging and analysis.
# 

# %% [code] Cell 14
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to a calculator, a Pakistani "
               "weather lookup, and a video game lookup. Use a tool whenever the user's "
               "question needs a calculation, weather data, or game info rather than "
               "answering from memory. State clearly when you don't have enough information."),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# %% [code] Cell 15
result = agent_executor.invoke({
    "input": "What's the weather in Lahore, and how long does it take to finish Hades?"
})

print(result["output"])

# %% [markdown] Cell 16
# ### Captured Multi-Step Agent Trace
# 
# The following trace was captured from the executed LangChain `AgentExecutor` with `verbose=True`. The user's request required both weather information and game information, so the agent selected two tools and used their returned observations to construct the final response.
# 
# **Reason / tool selection:** The agent identified that the request required weather data for Lahore and information about Hades.
# 
# **Action 1:** The agent invoked `get_weather` with `{"city": "Lahore"}`.
# 
# **Observation 1:** The tool returned `Lahore: Sunny, 38°C`.
# 
# **Action 2:** The agent invoked `lookup_game` with `{"title": "Hades"}`.
# 
# **Observation 2:** The tool returned Hades' release year, genre, developer, platforms, and average completion time of 21 hours.
# 
# **Final response:** The agent combined both tool observations into a natural-language answer.
# 
# The trace shows the same basic reason → act → observe pattern implemented manually in the raw-Python agent, but `AgentExecutor` now manages the loop and tool dispatch internally.
# 
# ### Comparison to the Raw-Python Agent
# 
# The overall workflow is similar to the raw-Python agent: the model determines which tool it needs, the tool executes, its result becomes an observation, and the model uses that observation to produce the next step or final answer. The main difference is that `AgentExecutor` manages this loop internally, so I no longer control or directly print every message and intermediate state.
# 
# In the raw-Python implementation, I explicitly built the message list and logged details such as the model response and tool results. With LangChain, `verbose=True` exposes the main execution events, including tool calls and their outputs, but lower-level details such as the exact formatted prompt and model metadata are not shown by default. I would need callbacks or additional tracing to inspect those details, which gives LangChain less manual code but also less immediate visibility into what happens internally.
# 
# 

# %% [markdown] Cell 17
# ## Task 4: Memory
# This section adds conversation memory using `RunnableWithMessageHistory`. The history store keeps messages for each session and makes those messages available to the agent through a `MessagesPlaceholder("chat_history")` in the prompt.

# %% [markdown] Cell 18
# ### Step 3: Add `MessagesPlaceholder("chat_history")` to the prompt
# 

# %% [code] Cell 19
memory_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to a calculator, a Pakistani "
               "weather lookup, and a video game lookup. Use a tool whenever the user's "
               "question needs a calculation, current weather, or game info rather than "
               "answering from memory. State clearly when you don't have enough information. "
               "Use the conversation history to resolve follow-up questions like 'that' or "
               "'the other one'."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])


# %% [markdown] Cell 20
# ### Step 4: Rebuild the Agent with the Updated Prompt
# 
# The prompt is supplied when `create_tool_calling_agent` constructs the agent, so the agent should be rebuilt after adding `MessagesPlaceholder("chat_history")`. The existing executor is also rebuilt with this new agent so that subsequent invocations use the updated prompt and can receive the stored conversation history.
# 

# %% [code] Cell 21
memory_agent = create_tool_calling_agent(llm, tools, memory_prompt)

memory_agent_executor = AgentExecutor(
    agent=memory_agent,
    tools=tools,
    verbose=True,
)

_store: dict[str, BaseChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]


agent_with_memory = RunnableWithMessageHistory(
    memory_agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# %% [markdown] Cell 22
# ### Step 5: Run the Three-Turn Memory Test
# 
# The three-turn test uses one session ID so that the agent receives the previous conversation history on each invocation. The first turn retrieves Hades' completion time, the second retrieves Portal 2 and compares it with the earlier game, and the third uses the information retained from the conversation to make a recommendation.
# 
# The executed trace shows that the agent retained Hades' 21-hour completion time and retrieved Portal 2's 8-hour completion time in the follow-up turn. The final turn then used both games from the conversation context to make a recommendation, confirming that the stored conversation history is reaching the agent and supporting follow-up questions.
# 

# %% [code] Cell 23
session_config = {
    "configurable": {
        "session_id": "memory-test-1"
    }
}
turn_1 = agent_with_memory.invoke(
    {"input": "How long does Hades take to finish?"},
    config=session_config,
)

print("TURN 1:")
print(turn_1["output"])

turn_2 = agent_with_memory.invoke(
    {"input": "What about Portal 2?"},
    config=session_config,
)

print("\nTURN 2:")
print(turn_2["output"])

turn_3 = agent_with_memory.invoke(
    {"input": "Which one should I recommend to a budget-conscious client?"},
    config=session_config,
)

print("\nTURN 3:")
print(turn_3["output"])

# %% [markdown] Cell 24
# ## Task 5: Structured Output and Error Handling
# 
# ### Step 6: Structured Final Output Produced by the Agent
# 
# The agent uses a `submit_recommendation` tool with a defined structured schema for its final recommendation. After gathering the required game information through `lookup_game`, the agent passes the recommendation fields to `submit_recommendation` instead of returning the result only as free-form text.
# 
# The structured result is validated against a Pydantic model, which ensures that the final recommendation follows the expected schema and contains the required fields. This integrates structured output directly into the agent's tool-use workflow and connects the final recommendation to information gathered from the game database.
# 

# %% [code] Cell 25
class GameRecommendation(BaseModel):
    game_a: str = Field(description="Name of the first game compared")
    game_b: str = Field(description="Name of the second game compared")
    recommendation: str = Field(description="Which game is recommended and why, in one sentence")
    confidence: str = Field(description="One of: low, medium, high")


@tool(args_schema=GameRecommendation)
def submit_recommendation(
    game_a: str,
    game_b: str,
    recommendation: str,
    confidence: str,
) -> str:
    """Submit the final structured recommendation after comparing two games.
    Use this tool only after looking up both games and deciding which one to recommend.
    Do not answer the comparison request only in free-form text.
    """
    return "Recommendation submitted."


structured_tools = tools + [submit_recommendation]

structured_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant with access to a calculator, a Pakistani "
        "weather lookup, a video game lookup, and a structured recommendation tool. "
        "Use tools whenever the user's question requires calculations, weather data, "
        "or game information. Do not call submit_recommendation when the user only "
        "asks for information or a comparison. In those cases, answer normally using "
        "the available tools. Call submit_recommendation only when the user explicitly "
        "asks you to choose, recommend, or pick one game. Never make a recommendation "
        "unless the current user request explicitly asks for one. Use conversation "
        "history to resolve follow-up references such as 'that', 'the other one', "
        "and 'which one'."
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

structured_agent = create_tool_calling_agent(
    llm,
    structured_tools,
    structured_prompt
)

structured_agent_executor = AgentExecutor(
    agent=structured_agent,
    tools=structured_tools,
    verbose=True,
    return_intermediate_steps=True,
)

structured_agent_with_memory = RunnableWithMessageHistory(
    structured_agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


def extract_structured_recommendation(result: dict):
    """Extract the GameRecommendation from the agent's submit_recommendation tool call."""
    for action, _observation in result.get("intermediate_steps", []):
        if action.tool == "submit_recommendation":
            return GameRecommendation(**action.tool_input)
    return None

# %% [markdown] Cell 26
# ### Step 7: Error Handling for an Unreliable Tool
# 
# The notebook includes a deliberately unreliable game-price lookup tool that raises a `ToolException` to simulate an intermittent external-service failure. The error is converted into a tool observation that the agent can see, allowing the agent to decide how to continue instead of terminating the entire execution.
# 
# The agent is configured with a limited number of iterations so it cannot retry indefinitely. This demonstrates a basic recovery pattern for tool failures: the tool reports the failure through the agent's normal tool-observation flow, and the model can retry, use another available tool, or report that the requested information could not be retrieved.
# 

# %% [code] Cell 27
@tool
def flaky_game_price_lookup(title: str) -> str:
    """Look up a game's sale price from an unreliable external storefront.
    The tool may fail intermittently and returns a recoverable error message.
    """
    try:
        if random.random() < 0.4:
            raise ToolException("storefront-api timeout")
        return f"{title}: price data unavailable in this demo, use lookup_game instead."
    except ToolException as e:
        return f"Tool error: {e}. Use lookup_game instead."

flaky_tools = tools + [flaky_game_price_lookup]

resilient_agent = create_tool_calling_agent(
    llm,
    flaky_tools,
    agent_prompt,
)

resilient_executor = AgentExecutor(
    agent=resilient_agent,
    tools=flaky_tools,
    verbose=True,
    max_iterations=6,
)



# %% [markdown] Cell 28
# ### Error-Handling Behavior
# 
# The `flaky_game_price_lookup` tool simulates an unreliable external storefront by occasionally raising a `ToolException`. Because the installed LangChain tool decorator does not support the `handle_tool_error` argument used by some examples, the tool catches the expected exception internally and converts it into a clear error message that becomes the tool's observation.
# 
# The agent can then continue from that observation and use `lookup_game` as a fallback or report that pricing information is unavailable. `max_iterations=6` provides an executor-level limit on the total number of agent/tool rounds, preventing the agent from retrying indefinitely.
# 

# %% [code] Cell 29
test_result = resilient_executor.invoke({
    "input": "What is the price of Hades?"
})

print(test_result["output"])

# %% [markdown] Cell 30
# ### Error-Handling Test Result
# 
# The error-handling test completed successfully. The `flaky_game_price_lookup` tool returned a message indicating that price data was unavailable and explicitly suggested using `lookup_game` as a fallback. The agent recognized this tool result, invoked `lookup_game` for Hades, and used the returned game information to provide a final response without terminating the execution.
# 
# This demonstrates graceful recovery at the tool level: an expected external-service failure is represented as a normal tool observation, allowing the agent to continue with an alternative tool. The executor also uses `max_iterations=6` as a hard limit on the total number of agent/tool rounds.
# 

# %% [markdown] Cell 31
# ### Step 8: Actual Agent Execution Trace
# 
# The following is the actual `verbose=True` trace captured from the LangChain agent during a multi-step request. The request required the agent to use both the weather and game-lookup tools before producing its final response.
# 
# The trace shows the observable execution sequence: the agent selects a tool, passes the required arguments, receives the tool result as an observation, and then continues until it can produce the final answer. LangChain does not expose the model's private chain-of-thought in this trace, so the reasoning is described only at the observable action and observation level.
# 
# **Action 1:** The agent invoked `get_weather` with the requested city.
# 
# **Observation 1:** The weather tool returned the corresponding weather data.
# 
# **Action 2:** The agent invoked `lookup_game` with the requested game title.
# 
# **Observation 2:** The game database returned the game's developer, release year, genre, platforms, and average completion time.
# 
# **Final response:** The agent combined the two tool results and returned the requested information to the user.
# 
# 

# %% [markdown] Cell 32
# ### Step 9: Final Integration Test
# 
# The final integration test runs the structured, memory-aware agent through a three-turn conversation using one session ID. The first turn retrieves information about Hades, the second uses conversation context to compare it with Portal 2, and the third asks the agent to recommend one of the games.
# 
# All three turns use `RunnableWithMessageHistory`, so conversation history is managed consistently rather than passed manually to the executor. The final turn is inspected for a `submit_recommendation` tool call, and its arguments are validated against the `GameRecommendation` Pydantic model.
# 
# A successful test confirms that conversation memory, tool calling, and structured output work together in the same agent workflow.
# 

# %% [code] Cell 33
session_id = "integration-test-1"
final_config = {"configurable": {"session_id": session_id}}

step_1 = structured_agent_with_memory.invoke(
    {"input": "How long does it take to finish Hades?"},
    config=final_config,
)

step_2 = structured_agent_with_memory.invoke(
    {"input": "Now compare that to Portal 2."},
    config=final_config,
)

step_3 = structured_agent_with_memory.invoke(
    {"input": "Which one should I pick if I only have a free afternoon?"},
    config=final_config,
)

print("Step 1:", step_1["output"])
print("Step 2:", step_2["output"])
print("Step 3:", step_3["output"])

final_recommendation = extract_structured_recommendation(step_3)

print("Structured result:", final_recommendation)

assert final_recommendation is not None, "Agent did not call submit_recommendation"
assert final_recommendation.confidence in {"low", "medium", "high"}

print("Integration test passed.")

# %% [markdown] Cell 34
# ### LangChain vs. the Raw-Python Agent: What Got Easier, What Got Leakier
# 
# LangChain made the agent loop much easier to implement because `AgentExecutor` handles tool-call parsing, tool dispatch, feeding observations back to the model, and stopping conditions that I previously implemented manually in the raw-Python agent. Tool registration also became simpler because `@tool` uses the function signature and docstring to expose the tool's interface instead of requiring a manually constructed tool schema. The main abstraction leak was visibility into the execution process: LangChain manages the prompt formatting, scratchpad, tool-calling flow, and memory wiring internally, so debugging can be harder when something does not behave as expected. The memory integration issue demonstrated this directly because history could be stored correctly while being omitted from the agent prompt, and additional details such as model metadata require explicit callbacks or tracing rather than the simple logging used in the raw-Python implementation.
# 
