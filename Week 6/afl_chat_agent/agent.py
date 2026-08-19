"""
Agent construction.

Uses OpenRouter as the primary model provider with Groq as a fallback, matching the provider
setup used elsewhere in this project. Requires OPENROUTER_API_KEY and GROQ_API_KEY in the
environment (a .env file is picked up automatically).
"""
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import SYSTEM_PROMPT
from langchain_tools import ALL_TOOLS

load_dotenv()

OPENROUTER_MODEL = "openai/gpt-4o-mini"
GROQ_MODEL = "openai/gpt-oss-120b"

def build_llm():
    primary = ChatOpenAI(
        model=OPENROUTER_MODEL,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
    )
    fallback = ChatOpenAI(
        model=GROQ_MODEL,
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
    )
    return primary.with_fallbacks([fallback])

# for testing I used groq alone
# import os
# from dotenv import load_dotenv

# from langchain_openai import ChatOpenAI
# #from langchain.agents import create_tool_calling_agent, AgentExecutor
# from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_community.chat_message_histories import ChatMessageHistory
# from langchain_core.runnables.history import RunnableWithMessageHistory

# from config import SYSTEM_PROMPT
# from langchain_tools import ALL_TOOLS

# load_dotenv()

# groq_model = "openai/gpt-oss-120b"

# def build_llm():
#     return ChatOpenAI(
#         model=groq_model,
#         base_url="https://api.groq.com/openai/v1",
#         api_key=os.environ["GROQ_API_KEY"],
#         temperature=0,
#     )


def build_agent_executor(verbose: bool = False) -> AgentExecutor:
    llm = build_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=ALL_TOOLS, verbose=verbose, return_intermediate_steps=True)


_store = {}


def _get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = ChatMessageHistory()
    return _store[session_id]


def build_conversational_agent(verbose: bool = False) -> RunnableWithMessageHistory:
    """
    Wraps the agent executor with per-session message history so multi-turn conversations
    ("what about the round before that?") resolve correctly without the caller re-sending
    prior turns manually.
    """
    executor = build_agent_executor(verbose=verbose)
    return RunnableWithMessageHistory(
        executor,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
