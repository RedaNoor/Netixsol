"""
Grounding verification.

Every stat-bearing answer should trace back to a real tool call. This module logs each tool
call and its return value during a conversation turn, then checks whether the numbers that show
up in the model's final answer actually appeared somewhere in a tool result. This doesn't prove
the model *used* the right number for the right reason, but it catches the most damaging failure
mode outright: a number in the answer that never came from any tool at all.
"""
import re
from langchain_core.callbacks import BaseCallbackHandler


class ToolCallLogger(BaseCallbackHandler):
    """Attach to an agent run to capture every tool call and its raw output."""

    def __init__(self):
        self.calls = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.calls.append({"tool": serialized.get("name"), "input": input_str, "output": None})

    def on_tool_end(self, output, **kwargs):
        if self.calls:
            self.calls[-1]["output"] = str(output)

    def reset(self):
        self.calls = []


_NUMBER_RE = re.compile(r"-?\d+\.?\d*")


def extract_numbers(text: str) -> list:
    """Pull out numeric tokens from a string, ignoring bare years-as-labels like '2024' in dates
    is not attempted here -- years are common in both tool outputs and legitimate answers, so
    they're left in; the check is intentionally permissive rather than trying to be clever about
    which numbers 'matter'."""
    return [float(n) for n in _NUMBER_RE.findall(text)]


def check_grounding(final_answer: str, tool_logger: ToolCallLogger) -> dict:
    """
    Cross-check the numbers in final_answer against everything returned by tool calls this turn.
    Returns a report: which numbers in the answer were found in some tool output, and which
    weren't (a red flag worth manual review, not an automatic fail -- small numbers like "5" or
    round numbers can coincidentally match, and some numbers in an answer are legitimately not
    stats, e.g. "here are 3 things").
    """
    answer_numbers = set(extract_numbers(final_answer))
    tool_output_text = " ".join(c["output"] or "" for c in tool_logger.calls)
    tool_numbers = set(extract_numbers(tool_output_text))

    grounded = answer_numbers & tool_numbers
    ungrounded = answer_numbers - tool_numbers

    return {
        "tool_calls_made": len(tool_logger.calls),
        "tools_used": [c["tool"] for c in tool_logger.calls],
        "numbers_in_answer": sorted(answer_numbers),
        "numbers_grounded_in_tool_output": sorted(grounded),
        "numbers_not_found_in_tool_output": sorted(ungrounded),
        "fully_grounded": len(ungrounded) == 0,
    }
