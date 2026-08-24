"""
Structured logging for the API layer — the foundation Task 4's monitoring plan reads from.
Every request produces one JSON log line with: query, detected intent, tools called, latency,
and token usage (when the underlying LLM call exposes it).
"""
import json
import logging
import time
import sys

logger = logging.getLogger("afl_api")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)


def log_request(conversation_id: str, query: str, intent: str, tools_called: list,
                 latency_ms: float, token_usage: dict, error: str = None):
    record = {
        "timestamp": time.time(),
        "conversation_id": conversation_id,
        "query": query,
        "intent": intent,
        "tools_called": tools_called,
        "latency_ms": round(latency_ms, 1),
        "token_usage": token_usage,
        "error": error,
    }
    logger.info(json.dumps(record, default=str))
    return record


def extract_token_usage(final_state: dict) -> dict:
    """
    Best-effort token usage extraction. LangChain message objects carry usage_metadata on the
    AIMessage when the provider returns it; this pulls it from the last AI message in state if
    present, and reports None rather than a fabricated number if it isn't.
    """
    messages = final_state.get("messages", [])
    for msg in reversed(messages):
        usage = getattr(msg, "usage_metadata", None)
        if usage:
            return {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                    "total_tokens": usage.get("total_tokens")}
    return {"input_tokens": None, "output_tokens": None, "total_tokens": None,
            "note": "not reported by this provider/call"}
