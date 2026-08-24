"""
State schema for the AFL LangGraph application.

One state object flows through every node. Fields are additive/overwritten as the graph
progresses — nothing gets mutated implicitly, each node returns exactly the keys it changed.
"""
from typing import TypedDict, Literal, Optional, Annotated
from langgraph.graph.message import add_messages


Intent = Literal["factual", "retrieval", "prediction_match", "prediction_player", "off_topic", "ambiguous"]


class AFLState(TypedDict, total=False):
    # conversation
    messages: Annotated[list, add_messages]   # full chat history (LangChain message objects)
    user_query: str                            # the current turn's raw input

    # routing
    intent: Intent
    router_confidence: float
    router_reasoning: str

    # entity resolution (populated by retrieval/prediction nodes before calling a tool)
    resolved_entities: dict                    # e.g. {"team_a": "Hawthorn Hawks", "date": "2025-08-20"}
    resolution_errors: list                    # human-readable strings, non-empty if resolution failed

    # tool execution
    tool_name: Optional[str]
    tool_result: Optional[dict]
    tool_error: Optional[str]

    # validation
    validation_passed: bool
    needs_clarification: bool
    clarification_question: Optional[str]

    # output
    final_response: str
