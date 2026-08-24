"""
Graph assembly for the AFL LangGraph application.

    START -> ingest -> router -> [direct_answer | retrieval | prediction | refusal | clarification]
                                        |              |            |
                                        v              v            v
                                    (END)        validation    validation
                                                       |             |
                                            [clarification | response_formatter]
                                                       |             |
                                                      (END)        (END, via finalize)

router picks one of 6 branches from intent. direct_answer/refusal/clarification (when reached
directly from an ambiguous router decision) set final_response themselves and skip validation —
there's no tool call to validate. retrieval and prediction always pass through validation, which
is the single place that decides "did this actually resolve, or does the user need to clarify."

Clarification is a same-turn response, not a graph-level pause: the question becomes this turn's
assistant message, and the loop happens across conversation turns via the checkpointer-persisted
message history — the next user message arrives with full prior context already in state, so a
follow-up like "Hawthorn Hawks, not just Hawks" resolves naturally without needing to re-ask.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AFLState
import nodes


def build_graph():
    g = StateGraph(AFLState)

    g.add_node("ingest", nodes.ingest_node)
    g.add_node("router", nodes.router_node)
    g.add_node("direct_answer", nodes.direct_answer_node)
    g.add_node("retrieval", nodes.retrieval_node)
    g.add_node("prediction", nodes.prediction_node)
    g.add_node("refusal", nodes.refusal_node)
    g.add_node("validation", nodes.validation_node)
    g.add_node("clarification", nodes.clarification_node)
    g.add_node("response_formatter", nodes.response_formatter_node)
    g.add_node("finalize", nodes.finalize_node)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "router")

    g.add_conditional_edges("router", nodes.route_from_intent, {
        "direct_answer": "direct_answer",
        "retrieval": "retrieval",
        "prediction": "prediction",
        "refusal": "refusal",
        "clarification": "clarification",
    })

    g.add_edge("retrieval", "validation")
    g.add_edge("prediction", "validation")
    g.add_conditional_edges("validation", nodes.route_from_validation, {
        "clarification": "clarification",
        "response_formatter": "response_formatter",
    })

    g.add_edge("direct_answer", "finalize")
    g.add_edge("refusal", "finalize")
    g.add_edge("clarification", "finalize")
    g.add_edge("response_formatter", "finalize")
    g.add_edge("finalize", END)

    return g.compile(checkpointer=MemorySaver())
