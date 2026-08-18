# -*- coding: utf-8 -*-
"""
Converted from IPYNB to PY
"""

# %% [markdown] Cell 1
# # Agent Foundations: Reasoning Loops, Tool Calling & Raw Python Agents
# 
# 
# Minimal ReAct-style agent built from scratch in raw Python, no framework
# (no LangChain, no LangGraph). 
# Uses OpenRouter's OpenAI-compatible API. 
# Key loaded from a `.env` file in the same folder as this notebook.

# %% [markdown] Cell 2
# ## Task 1: Agent Concepts & Mental Model
# 
# **Chatbot**: one turn in, one turn out. It answers from what it already
# knows or can generate. It has no way to go check something external or take
# an action, so if the answer needs new information, it either guesses or
# admits it doesn't know.
# 
# **Workflow**: a fixed sequence a human wrote ahead of time, step 1 then
# step 2 then step 3, always in that order. Reliable and predictable, but it
# can't adapt if something unexpected happens mid-sequence.
# 
# **Agent**: an LLM given tools and put in a loop, deciding at each step what
# to do next based on what it learned from earlier steps. The sequence of
# actions isn't fixed in advance, it's decided live as the task unfolds.
# 
# What makes something agentic:
# 
# 1. **Autonomy** - the model picks the next action, not a human or a script.
# 2. **Tool use** - it can act (call a function, hit an API), not just generate text.
# 3. **Multi-step planning** - it can break a goal into steps across several turns.
# 4. **Self-correction** - it can look at a result, notice it isn't enough, and try something else.
# 
# Quick test: if you removed the model's ability to choose the next step and
# hardcoded the sequence instead, would it still work? If yes, that was a
# workflow, not an agent.
# 

# %% [markdown] Cell 3
# 
# ### The ReAct pattern (Reason -> Act -> Observe -> repeat)
# 
# The model states what it needs next (**Reason**), calls a tool to get it
# (**Act**), reads what came back (**Observe**), and uses that to decide the
# next step. The loop stops once the model has enough to answer in plain text
# instead of calling another tool.
# 
# ```
#  USER REQUEST
#       v
# +-------------+
# |   REASON    |  "what do I need next?"
# +-------------+
#       v
# +-------------+
# |     ACT     |  call a tool (name + arguments)
# +-------------+
#       v
# +-------------+
# |   OBSERVE   |  read the tool's result
# +-------------+
#       v
#   enough info? --no--> back to REASON
#       |  
#      yes
#       |
#   FINAL ANSWER
# ```
# 
# Pseudocode:
# 
# ```
# messages = [user_request]
# loop:
#     response = model(messages, tools)
#     if response.finish_reason == "tool_calls":
#         result = run_tool(response.tool_name, response.tool_args)
#         messages.append(model's tool_call message)
#         messages.append(tool_result message)
#         continue
#     else:
#         return response.content   # final answer
# ```
# 
# ### When an agent is overkill
# 
# If the task is one lookup against a known API with a fixed number of steps
# ("get today's weather for this one city"), a direct function call does the
# same job for less latency, less cost, and no risk of the model looping or
# picking the wrong tool. An agent earns its cost only when the number of
# steps, or which tools are needed, depends on what earlier steps return and
# can't be hardcoded up front.

# %% [markdown] Cell 4
# ## Setup

# %% [code] Cell 5
import os
import re
import json

def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip().strip('"').strip("'")
    return env

env = load_env(".env")
# OPENROUTER_API_KEY = env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
# NVIDIA_API_KEY = env.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_API_KEY")
GROQ_API_KEY = env.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")

from openai import OpenAI
client = OpenAI(
    # base_url="https://openrouter.ai/api/v1",
    # api_key=OPENROUTER_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)
# MODEL = "openrouter/free"  # rotates across free models, filters for tool-calling support
# MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
# MODEL = "nvidia/llama-3.3-nemotron-70b-instruct"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = (
    "You have two tools available: calculator and get_weather. "
    "Always call the matching tool when the request needs a calculation or "
    "a weather lookup, never answer those from memory. If no tool applies "
    "to the request, say so directly instead of guessing. "
    "You are a tool-using assistant. Use available tools when required. "
    "Never invent tool results or assume missing information. "
    "Never guess, infer, or substitute a city when the user has not provided one. If a weather request does not specify a city, ask the user which city they mean. "
    "If a tool returns an ERROR, report that information is unavailable instead of guessing."
    "If no available tool can perform a task, say so clearly. Do not use emojis."
)

# %% [markdown] Cell 6
# ## Task 2: Tool Calling Fundamentals
# 
# A tool schema on OpenRouter follows the OpenAI function-calling format:
# `{"type": "function", "function": {"name", "description", "parameters"}}`.
# 
# `description` is the only thing the model has to work with when deciding
# whether a tool applies and how to fill in its arguments, it never sees the
# tool's source code. A vague description ("gets weather") leads to wrong
# tool choices and malformed arguments. Each description below states what
# the tool does, what each argument means, its format, and what it returns.

# %% [code] Cell 7
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluates a basic arithmetic expression and returns the numeric result. "
            "Supports +, -, *, /, parentheses, and decimals. Use this when the request "
            "requires computing a number rather than looking one up. Does not support "
            "variables or word problems, only a literal arithmetic expression."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A literal arithmetic expression, e.g. '(12 + 8) / 4'."
                }
            },
            "required": ["expression"]
        }
    }
}
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Looks up the current weather for a named city and returns the temperature "
            "in Celsius and a short condition summary. Use this when the request asks "
            "about current weather, temperature, or conditions in a specific place. "
            "The city must be a real city name, not coordinates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Lahore' or 'Karachi'."
                }
            },
            "required": ["city"]
        }
    }
}

tools = [calculator_tool, weather_tool]
print("Registered tools:", [t["function"]["name"] for t in tools])

# %% [markdown] Cell 8
# ### Tool functions

# %% [code] Cell 9
import ast
import operator

_ALLOWED_BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_ALLOWED_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def _safe_eval(node):
    if isinstance(node, ast.Expression): return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Div) and right == 0: raise ValueError("Division by zero.")
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS: return _ALLOWED_UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Only numbers, +, -, *, /, unary signs, and parentheses are allowed.")

def run_calculator(expression):
    if not isinstance(expression, str): raise ValueError("Expression must be a string.")
    expression = expression.strip()
    if not expression: raise ValueError("Expression cannot be empty.")
    if len(expression) > 200: raise ValueError("Expression is too long.")
    try:
        tree = ast.parse(expression, mode="eval")
        return _safe_eval(tree)
    except SyntaxError:
        raise ValueError(f"Not a valid arithmetic expression: '{expression}'")

fake_weather_db = {"perth": {"temp_c": 31, "condition": "sunny"}, "karachi": {"temp_c": 34, "condition": "hazy"}, "hobart": {"temp_c": 14, "condition": "cloudy"}, "melbourne": {"temp_c": 18, "condition": "windy"}}

def run_get_weather(city):
    if not isinstance(city, str): return "ERROR: city must be a string."
    city = city.strip()
    if not city: return "ERROR: city cannot be empty."
    key = city.lower()
    if key not in fake_weather_db: return f"ERROR: No weather data available for '{city}'."
    return fake_weather_db[key]

tool_functions = {"calculator": run_calculator, "get_weather": run_get_weather}

print("Tools ready:", list(tool_functions.keys()))

# %% [markdown] Cell 10
# ### Single tool call, executed manually

# %% [code] Cell 11
messages = [{"role": "user", "content": "What is (12 + 8) / 4?"}]
try:
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools, tool_choice="auto")
    choice = response.choices[0]
    if choice.finish_reason == "tool_calls":
        call = choice.message.tool_calls[0]
        args = json.loads(call.function.arguments)
        print("Model chose tool:", call.function.name)
        print("Arguments:", args)
        messages.append({"role": "assistant", "content": choice.message.content or "", "tool_calls": [{"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}}]})
        try:
            if call.function.name not in tool_functions: raise ValueError(f"Unknown tool: {call.function.name}")
            result = tool_functions[call.function.name](**args)
        except Exception as e:
            result = f"ERROR: {e}"
        print("Tool executed:", result)
        tool_result_message = {"role": "tool", "tool_call_id": call.id, "content": str(result)}
        messages.append(tool_result_message)
        print("Tool result sent back to model.")
        final_response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools, tool_choice="auto")
        final_answer = final_response.choices[0].message.content
        print("\nFinal answer:")
        print(final_answer)
    else:
        print("Model answered directly:")
        print(choice.message.content)
except Exception as e:
    print("Live tool-calling test failed.")
    print("Error type:", type(e).__name__)
    print("Error:", e)

# %% [code] Cell 12
print("CALCULATOR FAILURE TESTS")
print("=" * 40)
tests = [
    "10 / 0",
    "10 + abc",
    "",
    "2 ** 10",
    "(12 + 8) / 4"
]
for expression in tests:
    try:
        result = run_calculator(expression)
        print(f"{expression!r} -> {result}")
    except ValueError as e:
        print(f"{expression!r} -> HANDLED ERROR: {e}")

# %% [markdown] Cell 13
# ## Task 3: Build a Minimal Agent Loop

# %% [code] Cell 14
import re
import json

class Agent:
    def __init__(self, client, model, tools, tool_functions, max_iterations=6, verbose=True):
        self.client = client
        self.model = model
        self.tools = tools
        self.tool_functions = tool_functions
        self.max_iterations = max_iterations
        self.verbose = verbose

    def log(self, label, message):
        if self.verbose: print(f"[{label}] {message}")

    def run(self, user_message):
        messages = [{"role": "system", "content": "You are a tool-using assistant. Use available tools when required."}, {"role": "user", "content": user_message}]
        self.log("USER", user_message)
        step = 0

        while step < self.max_iterations:
            step += 1
            self.log("STEP", f"{step}/{self.max_iterations}")

            try:
                response = self.client.chat.completions.create(model=self.model, messages=messages, tools=self.tools, tool_choice="auto")
            except Exception as e:
                self.log("ERROR", f"Model call failed: {e}")
                return "The agent could not complete the request because the model call failed."

            choice = response.choices[0]
            msg = choice.message
            self.log("MODEL", response.model)

            if choice.finish_reason != "tool_calls":
                final_text = msg.content or ""
                self.log("FINAL", final_text)
                return final_text

            if not msg.tool_calls:
                self.log("ERROR", "No tool call was returned.")
                return "The model returned an invalid tool call."

            tc = msg.tool_calls[0]
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}]})
            name = tc.function.name

            try:
                args = json.loads(tc.function.arguments)
                self.log("ACT", f"calling {name}({args})")
                if name not in self.tool_functions: raise ValueError(f"Unknown tool requested: {name}")
                result = self.tool_functions[name](**args)
                self.log("OBSERVE", f"{name} -> {result}")
            except Exception as e:
                result = f"ERROR: {e}"
                self.log("OBSERVE", f"{name} -> {result}")

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

        self.log("STOP", "max_iterations reached without a final answer.")
        return "I could not complete the task within the maximum number of allowed steps."

print("Agent class defined.")

# %% [markdown] Cell 15
# ### Multi-step test, 2+ tool calls

# %% [code] Cell 16
agent = Agent( client=client, model=MODEL, tools=tools, tool_functions=tool_functions, max_iterations=6, verbose=True)
agent.run(
    "Look up the weather in Perth and Hobart and tell me which is warmer.")

# %% [markdown] Cell 17
# ## Task 4: Memory & State Handling
# 
# **Conversation memory** is the `messages` list, the literal transcript of
# system, user, assistant, and tool turns. It's sent in full on every call
# because the API is stateless between requests, it's the agent's only
# record of what already happened.
# 
# **Working memory** (scratchpad) is anything the agent tracks about the task
# itself, separate from the raw transcript: a running plan, intermediate
# computed values, a list of remaining sub-steps. Conversation memory grows
# automatically just by talking. Working memory has to be deliberately
# designed, without it the agent can only "remember" by re-reading the whole
# transcript each call, which gets expensive and unreliable as tasks get
# longer. `Agent` above only has conversation memory, no separate scratchpad,
# fine for a two-step task, would start to strain past ten or so sequential
# sub-goals.
# 
# The `self.log(...)` calls print every reason, act, and observe step as it
# happens, plus which model answered. That's the debugging habit worth
# keeping once a framework is doing the looping instead of this notebook.

# %% [markdown] Cell 18
# ## Task 5: Failure Modes & Guardrails
# 
# Five deliberate break attempts: an ambiguous request, a tool call with a
# bad argument, a request needing a tool that was never registered, a
# request with no matching tool at all, and a tight `max_iterations` cap on
# a task that needs more steps than that.

# %% [code] Cell 19
print(agent.run("What is the weather like there?"))

# %% [code] Cell 20
print(agent.run("What is the weather in Atlantis?"))

# %% [code] Cell 21
print(agent.run("Read notes.txt and summarize it."))

# %% [code] Cell 22
# no tool covers this at all, neither calculator nor get_weather applies
print(agent.run("What will Tesla's stock price be tomorrow?"))

# %% [code] Cell 23
tight_agent = Agent(client, MODEL, tools, tool_functions, max_iterations=2, verbose=True)
print(tight_agent.run("Look up the weather for Perth, Hobart, Karachi, and Melbourne and rank them by temperature."))

# %% [markdown] Cell 24
# ### Failure modes and mitigations
# 
# | Failure mode | Cause | Mitigation |
# |---|---|---|
# | Infinite / runaway loop | Model never returns a final answer | `max_iterations` hard cap, loop returns `None` instead of hanging |
# | Hallucinated tool call | Model calls a tool name that was never registered | Executor checks the name against `tool_functions` and raises a caught error |
# | Hallucinated answer, no tool call | Model answers a weather/calculation question from memory instead of calling the tool, seen live when Karachi returned London's weather | `SYSTEM_PROMPT` explicitly instructs the model to always call the matching tool and never answer those from memory |
# | Wrong / bad tool arguments | Model passes a value the tool can't resolve (unsupported city) | Tool raises a normal exception, caught and turned into an `ERROR:` tool message, model gets a chance to recover next turn |
# | Invalid calculator input | Invalid expressions can cause tool errors |Validate calculator input and return clear ERROR: messages |
# | Out-of-scope request | Request needs neither tool (e.g. a stock price) | `SYSTEM_PROMPT` tells the model to say so directly instead of guessing |
# | Silent errors | A failed tool call could look identical to a correct one in the final answer | Every reason, act, and observe step is logged, failures show up in the transcript |
# 
# ### Why frameworks like LangChain, LangGraph, and CrewAI exist
# 
# The loop, schemas, and executor above are under 200 lines, and that already
# needed care around max iterations, error handling, input validation, and
# model compliance. Frameworks exist because real systems need many tools,
# multiple cooperating agents, long-running state that survives a restart,
# streaming output, and retries, and that plumbing is mostly the same across
# projects. A framework packages it once so teams build the parts specific
# to their product (which tools, what the agent should do) instead of
# re-solving "how do I safely run a while-loop with tool calls" every time.
# Having built it by hand first, including hitting the hallucinated-answer
# bug directly, means that when a framework's abstraction does something
# unexpected, the underlying mechanism is already understood.
