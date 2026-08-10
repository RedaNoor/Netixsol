# Agent Foundations

## Goal

Build a minimal LLM agent from scratch in raw Python before using agent frameworks such as LangChain, LangGraph, or CrewAI.

The notebook demonstrates the core agent loop: the model receives a task, selects a tool when needed, observes the tool result, and continues until it produces a final answer.

## Tasks Covered

### Task 1: Agent Concepts and Mental Model

The notebook explains:

- Agent vs chatbot vs workflow.
- What makes a system agentic: autonomy, tool use, multi-step planning, and self-correction.
- The ReAct pattern: Reason → Act → Observe → repeat.
- Situations where an agent is unnecessary and a simple prompt or script is better.

### Task 2: Tool Calling Fundamentals

Two local tools are implemented:

1. `calculator`
2. `get_weather`

The tools use JSON schemas containing:

- Tool name.
- Description.
- Input schema.
- Required arguments.

The notebook demonstrates a model selecting a tool, Python executing it, and the tool result being returned to the model.

### Task 3: Minimal Raw-Python Agent

The `Agent` class implements the core loop using a Python `while` loop:

```text
User request
    ↓
LLM call
    ↓
Tool call?
 ┌──┴──┐
No    Yes
 ↓      ↓
Final  Execute tool
answer    ↓
       Tool result
           ↓
        LLM call
           ↓
        Repeat
```

The implementation includes a `max_iterations` safeguard so the agent cannot run indefinitely.

The multi-step weather test requires more than one tool call and compares the weather in Perth and Hobart.

## Task 4: Memory and State

The notebook distinguishes between:

- Conversation memory: the `messages` list containing the conversation and tool results.
- Working state: information tracked during the current agent execution.
- Logging: `[USER]`, `[STEP]`, `[MODEL]`, `[ACT]`, `[OBSERVE]`, `[FINAL]`, and `[STOP]` messages used to inspect the agent's execution.

## Task 5: Failure Modes and Guardrails

The notebook tests and discusses several failure cases:

- Ambiguous requests with missing city information.
- Unknown weather locations.
- Calculator errors.
- Unsupported operations.
- Missing tools.
- Model/API tool-call failures.
- Infinite or runaway loops.

The calculator validates expressions using Python's AST module instead of directly executing arbitrary input with `eval()`.

Tool execution is wrapped in exception handling so errors are returned to the agent instead of silently crashing the loop.

## API Provider

The notebook was originally designed to use **OpenRouter** as the API provider.

Groq was used temporarily during testing because it provided a convenient OpenAI-compatible endpoint for testing tool calling.

The original provider configuration is:

```text
Provider: OpenRouter
Endpoint: https://openrouter.ai/api/v1
```

The exact model can be selected through the `MODEL` variable in the notebook.

The OpenAI Python package is used as the client library because OpenRouter provides an OpenAI-compatible API. This does not mean the notebook uses the OpenAI API.

## Environment Setup

Create a `.env` file locally:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

During temporary Groq testing, the notebook may instead use:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do not commit the `.env` file or expose any API key in the notebook.

Do not commit the `.env` file or expose the API key in the notebook.

Install the required packages if necessary:

```bash
pip install openai python-dotenv
```

## Project Structure

```text
Week5_Day1/
├── agent_foundations.ipynb
├── README.md
└── .env
```

The `.env` file should remain local and should not be submitted to version control.

## Key Implementation Decisions

### Raw Python instead of an agent framework

The agent is implemented without LangChain, LangGraph, or CrewAI so the underlying mechanics remain visible.

### AST-based calculator

The calculator parses arithmetic expressions into an AST and evaluates only approved numeric and arithmetic nodes.

This avoids directly executing arbitrary Python expressions with `eval()`.

### Local weather stub

Weather data is intentionally stored in a small local dictionary.

This keeps the exercise focused on tool calling rather than external weather APIs.

### Maximum iteration limit

The agent stops after a fixed number of iterations.

This prevents an incorrectly behaving model from producing an uncontrolled tool-calling loop.

### Tool error handling

Tool execution is wrapped in exception handling.

Errors are converted into tool observations so the model can respond appropriately instead of the Python process failing silently.

## Expected Outcome

After running the notebook, you should be able to explain and demonstrate:

1. What an LLM agent is.
2. How tool/function calling works.
3. How JSON tool schemas guide model tool selection.
4. How a ReAct-style loop works.
5. How conversation state is maintained.
6. How tool failures are handled.
7. Why iteration limits and guardrails are necessary.
8. Why agent frameworks exist after understanding the raw implementation.

## Known Limitation

The weather tool is a stub and does not provide live weather information.

The notebook was tested temporarily with Groq, so some observed tool-calling behavior is provider/model-specific. A model or API provider may reject malformed or unsupported tool-call generations before the local Python tool receives them. This is a provider/model-level failure and is documented as part of the failure-mode analysis.

## Conclusion

This notebook builds the basic mechanics that agent frameworks automate: model interaction, tool selection, tool execution, state management, iteration, logging, and failure handling.

Understanding these mechanics first makes framework-based agents easier to debug and reason about later.
