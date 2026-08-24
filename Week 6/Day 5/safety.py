"""
System hardening utilities shared across every node and tool call.

Two failure modes get handled the same way everywhere rather than ad hoc per node:
1. A tool or LLM call hangs or takes too long -> enforced timeout, converted to a normal
   tool_error the validation node already knows how to handle (not a crash).
2. A node raises an unexpected exception -> caught, logged, converted to a graceful
   clarification-style response instead of taking the whole graph invocation down.
"""
import time
import logging
import functools
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger("afl_agent")

DEFAULT_TOOL_TIMEOUT_SECONDS = 12
DEFAULT_LLM_TIMEOUT_SECONDS = 20

_executor = ThreadPoolExecutor(max_workers=8)


class ToolTimeoutError(Exception):
    pass


def call_with_timeout(fn, *args, timeout_seconds=DEFAULT_TOOL_TIMEOUT_SECONDS, **kwargs):
    """Runs fn(*args, **kwargs) with a hard wall-clock timeout. Raises ToolTimeoutError on
    expiry rather than letting a slow tool call or LLM request hang the whole conversation
    turn indefinitely."""
    future = _executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        raise ToolTimeoutError(f"'{getattr(fn, '__name__', str(fn))}' did not respond within {timeout_seconds}s.")


def safe_node(node_name: str):
    """
    Decorator applied to every graph node. Catches any unhandled exception, logs it with
    timing, and returns a safe partial-state update (a tool_error the validation node already
    understands, or — for nodes with no validation step downstream — a direct clarification-
    style final_response) instead of letting the exception propagate and crash the request.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.monotonic() - start
                logger.info(f"node={node_name} status=ok latency_ms={elapsed*1000:.0f}")
                return result
            except ToolTimeoutError as e:
                elapsed = time.monotonic() - start
                logger.warning(f"node={node_name} status=timeout latency_ms={elapsed*1000:.0f} error={e}")
                return {"tool_error": str(e), "resolution_errors": [str(e)]}
            except Exception as e:
                elapsed = time.monotonic() - start
                logger.error(f"node={node_name} status=error latency_ms={elapsed*1000:.0f} error={e}", exc_info=True)
                return {
                    "tool_error": f"Internal error in {node_name}: {e}",
                    "resolution_errors": [f"Something went wrong processing that request."],
                    "final_response": (
                        "Something went wrong on my end processing that — could you try "
                        "rephrasing, or ask about a different team, player, or match?"
                    ),
                }
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Abuse / probing tracking — in-memory, per conversation thread
# ---------------------------------------------------------------------------
_offtopic_counts = {}
OFFTOPIC_ESCALATION_THRESHOLD = 4


def track_offtopic_attempt(thread_id: str) -> int:
    """Increments and returns the off-topic attempt count for this thread. Used to detect
    repeated probing (someone testing scope boundaries or trying variations of a jailbreak)
    rather than a one-off off-topic question, which is normal and not worth flagging."""
    _offtopic_counts[thread_id] = _offtopic_counts.get(thread_id, 0) + 1
    count = _offtopic_counts[thread_id]
    if count >= OFFTOPIC_ESCALATION_THRESHOLD:
        logger.warning(f"thread={thread_id} repeated_offtopic_attempts={count} — possible scope-probing pattern")
    return count


def reset_offtopic_count(thread_id: str):
    _offtopic_counts.pop(thread_id, None)
