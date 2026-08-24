"""
Runs the 10 end-to-end conversations against the compiled graph. For conversations marked
trace=True, logs the full node-by-node state trace (router decision -> tool called ->
validation -> final response) to reports/traces/. For all conversations, writes a summary log.

Run: python tests/run_e2e_tests.py
Output: reports/e2e_summary.md, reports/traces/<id>.md (annotated)
"""
import sys
import json
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph import build_graph
from tests.e2e_conversations import CONVERSATIONS

REPORTS_DIR = Path(__file__).parent.parent / "reports"
TRACES_DIR = REPORTS_DIR / "traces"
REPORTS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)

NODE_ANNOTATIONS = {
    "ingest": "conversation history updated with the new user message",
    "router": "intent classified",
    "direct_answer": "general AFL knowledge answered directly, no tool call",
    "retrieval": "structured retrieval tool selected and called",
    "prediction": "entities extracted, resolved, and prediction model called",
    "refusal": "off-topic — deterministic refusal message returned",
    "validation": "checked whether the tool call actually resolved cleanly",
    "clarification": "validation failed or intent was ambiguous — asking the user for more detail",
    "response_formatter": "tool result turned into natural language, disclaimer applied if a prediction",
    "finalize": "response appended to conversation history",
}


def _summarize_value(v, max_len=300):
    s = json.dumps(v, default=str) if not isinstance(v, str) else v
    return s if len(s) <= max_len else s[:max_len] + "...(truncated)"


def run_traced_turn(app, user_query, thread_id):
    """Runs one turn, returns (final_response, trace_lines)."""
    config = {"configurable": {"thread_id": thread_id}}
    trace_lines = [f"### Turn: \"{user_query}\""]
    final_response = None

    for update in app.stream({"user_query": user_query}, config=config, stream_mode="updates"):
        for node_name, node_output in update.items():
            if node_output is None:
                continue
            annotation = NODE_ANNOTATIONS.get(node_name, "")
            trace_lines.append(f"\n**Node: `{node_name}`** — {annotation}")
            for key, value in node_output.items():
                if key == "messages":
                    continue
                trace_lines.append(f"- `{key}`: {_summarize_value(value)}")
            if node_name == "finalize":
                final_response = node_output.get("messages", [None])[0]
                final_response = getattr(final_response, "content", str(final_response))

    return final_response, trace_lines


def run_plain_turn(app, user_query, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke({"user_query": user_query}, config=config)
    return result["final_response"]


def main():
    app = build_graph()
    summary_lines = ["# End-to-End Test Summary", ""]

    for convo in CONVERSATIONS:
        thread_id = f"{convo['id']}-{uuid.uuid4().hex[:6]}"
        print(f"\n=== {convo['id']} ({convo['path']}) ===")
        summary_lines.append(f"## {convo['id']} — {convo['path']}")

        if convo["trace"]:
            trace_lines = [f"# Trace: {convo['id']} — {convo['path']}", ""]
            for turn in convo["turns"]:
                response, lines = run_traced_turn(app, turn, thread_id)
                trace_lines.extend(lines)
                trace_lines.append(f"\n**Final response:** {response}\n")
                print(f"  User: {turn}")
                print(f"  Assistant: {response}")
                summary_lines.append(f"- User: {turn}")
                summary_lines.append(f"  Assistant: {response}")
            with open(TRACES_DIR / f"{convo['id']}.md", "w") as f:
                f.write("\n".join(trace_lines))
        else:
            for turn in convo["turns"]:
                response = run_plain_turn(app, turn, thread_id)
                print(f"  User: {turn}")
                print(f"  Assistant: {response}")
                summary_lines.append(f"- User: {turn}")
                summary_lines.append(f"  Assistant: {response}")

        summary_lines.append("")

    with open(REPORTS_DIR / "e2e_summary.md", "w") as f:
        f.write("\n".join(summary_lines))
    print(f"\nWritten to {REPORTS_DIR}/e2e_summary.md and {TRACES_DIR}/")


if __name__ == "__main__":
    main()
