# LangChain Agent: Tools, Chains, Memory and Structured Output

A LangChain rebuild of an earlier raw-Python ReAct agent. Adds LCEL chains, conversation memory, a local game database lookup, structured output via a Pydantic-backed tool, and basic tool-failure handling. Uses Groq as the LLM provider through `ChatGroq`.

## Project structure

```
.
├── langchain_agent.ipynb        # main notebook (setup, tools, agent, memory, structured output)
├── Writeup.pdf
├── data/
│   └── games.json               # local game database used by the lookup_game tool
├── .env                         # holds GROQ_API_KEY (and optionally OPENROUTER_API_KEY)
└── README.md
```

`data/games.json` is required before running the tool-definition cell. It should be a JSON array of game objects, each with at least:

```json
{
  "title": "Hades",
  "developer": "Supergiant Games",
  "release_year": 2020,
  "genre": "Roguelike",
  "platform": "PC, Switch, PS5, Xbox Series X/S",
  "avg_completion_hours": 21
}
```

## Setup

1. Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=your_key_here
   ```
   An OpenRouter fallback (`OPENROUTER_API_KEY`) is supported and commented out in the notebook if Groq gets rate-limited; swapping providers does not require changing the rest of the agent code.
2. Install dependencies (first code cell in the notebook):
   ```
   pip install -U langchain langchain-community langchain-groq langchain-classic python-dotenv
   ```
3. Confirm `data/games.json` exists before running the tool cells, `lookup_game` reads it at import time and will fail on a missing file rather than falling back silently.

## What's in the notebook

- **Task 1, Setup and concepts**: maps each raw-Python agent component to its LangChain equivalent, then builds a minimal `prompt | llm | StrOutputParser()` LCEL chain.
- **Task 2, Tools**: `calculator` (regex-validated arithmetic), `get_weather` (fixed lookup table for Pakistani cities), and `lookup_game` (reads `data/games.json`, supports exact and unambiguous partial title matches). Each tool is unit-tested directly with `.invoke()` before being handed to an agent.
- **Task 3, Agent and trace**: builds the tool-calling agent with `create_tool_calling_agent` + `AgentExecutor`, runs a multi-tool request, and includes an annotated action/observation trace plus a written comparison against the raw-Python loop.
- **Task 4, Memory**: adds `MessagesPlaceholder("chat_history")` and wires up `RunnableWithMessageHistory` with an in-memory, session-keyed history store. Runs a three-turn conversation to confirm follow-up questions resolve correctly against prior turns.
- **Task 5, Structured output and error handling**: adds a `submit_recommendation` tool backed by a `GameRecommendation` Pydantic model so the agent's final recommendation is schema-validated instead of free text, plus a deliberately unreliable `flaky_game_price_lookup` tool to demonstrate recovering from a tool-level failure without crashing the run. Closes with a three-turn integration test that exercises memory, tool calls, and structured output together.
