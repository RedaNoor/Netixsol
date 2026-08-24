"""
Node implementations for the AFL LangGraph application.

Each node is a small, single-purpose function: state in, partial state update out. The
philosophy driving this file (see README for the full argument) is that routing, disclaimers,
and refusals are handled by deterministic Python here, not left to an LLM's judgment on every
turn — the LLM's job is narrowly scoped to classification, entity extraction, and prose
generation, never to deciding whether a disclaimer is warranted.
"""
import os
import json
from typing import Optional, Literal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

import config
from state import AFLState
from langchain_tools import ALL_TOOLS as RETRIEVAL_TOOLS
from prediction_tools import predict_match_winner_tool, predict_top_player_tool
import entity_resolution as er
import predict

OPENROUTER_MODEL = "openai/gpt-4o-mini"
GROQ_MODEL = "llama-3.1-70b-versatile"


def build_llm(temperature: float = 0):
    primary = ChatOpenAI(
        model=OPENROUTER_MODEL, base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"], temperature=temperature,
    )
    fallback = ChatOpenAI(
        model=GROQ_MODEL, base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"], temperature=temperature,
    )
    return primary.with_fallbacks([fallback])


# ---------------------------------------------------------------------------
# Ingest / finalize — keep state["messages"] as the single source of conversation history.
# Every other node reads messages[-6:] for context; nothing re-derives history from user_query.
# ---------------------------------------------------------------------------
def ingest_node(state: AFLState) -> dict:
    return {"messages": [HumanMessage(content=state["user_query"])]}


def finalize_node(state: AFLState) -> dict:
    return {"messages": [AIMessage(content=state["final_response"])]}


# ---------------------------------------------------------------------------
# Router node
# ---------------------------------------------------------------------------
class RouterOutput(BaseModel):
    intent: Literal["factual", "retrieval", "prediction_match", "prediction_player", "off_topic", "ambiguous"]
    confidence: float = Field(description="0-1 confidence in this classification")
    reasoning: str = Field(description="one short sentence explaining the classification")


def router_node(state: AFLState) -> dict:
    llm = build_llm().with_structured_output(RouterOutput)
    history = state.get("messages", [])[-6:]  # already ends with this turn's HumanMessage (see ingest_node)
    messages = [SystemMessage(content=config.ROUTER_SYSTEM_PROMPT)] + history
    result = llm.invoke(messages)
    return {
        "intent": result.intent,
        "router_confidence": result.confidence,
        "router_reasoning": result.reasoning,
    }


def route_from_intent(state: AFLState) -> str:
    """Conditional edge function: maps intent -> next node name."""
    intent = state.get("intent", "ambiguous")
    return {
        "factual": "direct_answer",
        "retrieval": "retrieval",
        "prediction_match": "prediction",
        "prediction_player": "prediction",
        "off_topic": "refusal",
        "ambiguous": "clarification",
    }.get(intent, "clarification")


# ---------------------------------------------------------------------------
# Direct-answer node (general AFL knowledge, no tool needed)
# ---------------------------------------------------------------------------
def direct_answer_node(state: AFLState) -> dict:
    llm = build_llm(temperature=0.3)
    history = state.get("messages", [])[-6:]
    messages = [SystemMessage(content=config.DIRECT_ANSWER_SYSTEM_PROMPT)] + history
    response = llm.invoke(messages)
    return {"final_response": response.content, "validation_passed": True}


# ---------------------------------------------------------------------------
# Retrieval node
# ---------------------------------------------------------------------------
RETRIEVAL_SYSTEM_PROMPT = """Call the single most appropriate tool to answer the question using
real data. Resolve team/player names as best you can from the conversation context. If nothing
in the tool list actually answers this question, do not call a tool."""


def retrieval_node(state: AFLState) -> dict:
    llm = build_llm().bind_tools(RETRIEVAL_TOOLS)
    history = state.get("messages", [])[-6:]
    messages = [SystemMessage(content=RETRIEVAL_SYSTEM_PROMPT)] + history
    ai_msg = llm.invoke(messages)

    if not getattr(ai_msg, "tool_calls", None):
        return {"tool_error": "No matching retrieval tool was called.",
                "resolution_errors": ["Could not determine what to look up from this question."]}

    call = ai_msg.tool_calls[0]
    tool_map = {t.name: t for t in RETRIEVAL_TOOLS}
    tool_fn = tool_map.get(call["name"])
    if tool_fn is None:
        return {"tool_error": f"Model called unknown tool '{call['name']}'."}

    try:
        result = tool_fn.invoke(call["args"])
        return {"tool_name": call["name"], "tool_result": result, "tool_error": None,
                "resolved_entities": call["args"]}
    except Exception as e:
        return {"tool_name": call["name"], "tool_error": str(e), "resolved_entities": call["args"]}


# ---------------------------------------------------------------------------
# Prediction node
# ---------------------------------------------------------------------------
class MatchEntities(BaseModel):
    team_a: str = Field(description="first team mentioned (treated as home if order is ambiguous)")
    team_b: str = Field(description="second team mentioned")
    date_mention: Optional[str] = Field(default=None,
        description="a date or relative reference like 'this week' if mentioned, else null")


class PlayerEntities(BaseModel):
    team: str = Field(description="the team whose players are being asked about")
    stat_type: str = Field(default="fantasy_points",
        description="'fantasy_points', 'disposals', or 'goals' based on what was asked; default fantasy_points")
    date_mention: Optional[str] = Field(default=None)


def prediction_node(state: AFLState) -> dict:
    llm = build_llm()
    history = state.get("messages", [])[-6:]
    intent = state["intent"]

    if intent == "prediction_match":
        extractor = llm.with_structured_output(MatchEntities)
        ents = extractor.invoke(history)
        result = predict_match_winner_tool.invoke({
            "team_a": ents.team_a, "team_b": ents.team_b, "date": ents.date_mention})
        resolved = {"team_a_mention": ents.team_a, "team_b_mention": ents.team_b}
    else:
        extractor = llm.with_structured_output(PlayerEntities)
        ents = extractor.invoke(history)
        result = predict_top_player_tool.invoke({
            "team": ents.team, "stat_type": ents.stat_type, "date": ents.date_mention})
        resolved = {"team_mention": ents.team, "stat_type": ents.stat_type}

    if "error" in result:
        return {"tool_error": result["error"], "resolved_entities": resolved,
                "resolution_errors": [result["error"]], "tool_result": result}

    return {"tool_name": f"predict_{intent.split('_')[1]}", "tool_result": result,
            "tool_error": None, "resolved_entities": resolved}


# ---------------------------------------------------------------------------
# Refusal node — deterministic, not LLM-generated, so scope enforcement can't drift
# ---------------------------------------------------------------------------
def refusal_node(state: AFLState) -> dict:
    return {"final_response": config.REFUSAL_MESSAGE, "validation_passed": True}


# ---------------------------------------------------------------------------
# Validation node
# ---------------------------------------------------------------------------
def validation_node(state: AFLState) -> dict:
    if state.get("tool_error") or state.get("resolution_errors"):
        result = state.get("tool_result") or {}
        error_type = result.get("error_type")

        if error_type == "team_resolution":
            suggestions = result.get("suggestions") or []
            clause = f" Did you mean: {', '.join(suggestions)}?" if suggestions else " Which AFL club did you mean?"
            q = config.CLARIFICATION_TEMPLATES["team_not_resolved"].format(
                text=result.get("unresolved", "that team"), suggestion_clause=clause)
        elif error_type == "unsupported_stat":
            q = config.CLARIFICATION_TEMPLATES["unsupported_stat"].format(stat=result.get("stat_type", "that stat"))
        elif error_type == "same_team":
            q = result.get("error", "I need two different teams to compare.")
        else:
            q = ("I couldn't find what you're after with the data I have. Could you rephrase, "
                 "or give me a specific team, player, or date?")

        return {"validation_passed": False, "needs_clarification": True, "clarification_question": q}

    return {"validation_passed": True, "needs_clarification": False}


def route_from_validation(state: AFLState) -> str:
    return "clarification" if state.get("needs_clarification") else "response_formatter"


# ---------------------------------------------------------------------------
# Clarification node
# ---------------------------------------------------------------------------
def clarification_node(state: AFLState) -> dict:
    question = state.get("clarification_question")
    if not question:
        # reached directly from an "ambiguous" router intent, no specific question generated yet
        question = ("I want to make sure I get this right — could you give me a bit more detail? "
                     "(e.g. which team, player, or season you mean)")
    return {"final_response": question, "validation_passed": True}


# ---------------------------------------------------------------------------
# Response formatter node
# ---------------------------------------------------------------------------
FORMATTER_SYSTEM_PROMPT = """Turn this tool result into a natural, conversational answer. State
only facts present in the tool result — never add, round, or infer a number that isn't there.
Keep it concise.
"""

PREDICTION_FORMATTER_SYSTEM_PROMPT = """Turn this prediction result into a natural,
conversational answer. Report the probability/predicted value and the top factors from
'explanation' in plain language. Do not state the outcome as certain — always frame it as a
statistical estimate. Keep it concise.
"""


def response_formatter_node(state: AFLState) -> dict:
    if state.get("final_response"):
        return {}  # already set by refusal/clarification/direct_answer nodes

    intent = state.get("intent")
    tool_result = state.get("tool_result", {})
    is_prediction = intent in ("prediction_match", "prediction_player")

    llm = build_llm(temperature=0.2)
    system = PREDICTION_FORMATTER_SYSTEM_PROMPT if is_prediction else FORMATTER_SYSTEM_PROMPT
    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"User asked: {state['user_query']}\n\nTool result:\n{json.dumps(tool_result, default=str)}"),
    ]
    response = llm.invoke(messages)
    text = response.content

    if is_prediction:
        text = f"{text}\n\n{config.PREDICTION_DISCLAIMER}"

    return {"final_response": text}
