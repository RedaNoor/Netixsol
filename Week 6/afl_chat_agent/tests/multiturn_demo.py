"""
Task 4 — multi-turn conversation test.

Covers a team, then a player on that team, then a stat comparison, then a follow-up that
requires resolving "that season" and "him" from earlier turns without repeating context.

Run: python tests/multiturn_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import build_conversational_agent
from grounding import ToolCallLogger, check_grounding

SESSION_ID = "multiturn-demo"

CONVERSATION = [
    "Tell me about Hawthorn's 2024 season.",
    "Who had the best fantasy output for them that year?",
    "What's his career average by comparison?",
    "How does that stack up against Patrick Dangerfield's numbers in the same year?",
    "And what was Hawthorn's head-to-head record against Geelong that season?",
]


def main():
    conv_agent = build_conversational_agent(verbose=False)

    for i, turn in enumerate(CONVERSATION, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {turn}")

        logger = ToolCallLogger()
        result = conv_agent.invoke(
            {"input": turn},
            config={"configurable": {"session_id": SESSION_ID}, "callbacks": [logger]},
        )
        answer = result["output"]
        print(f"Assistant: {answer}")

        if logger.calls:
            report = check_grounding(answer, logger)
            print(f"  tools called: {report['tools_used']}")
            if not report["fully_grounded"]:
                print(f"  WARNING — numbers not traced to a tool call: "
                      f"{report['numbers_not_found_in_tool_output']}")


if __name__ == "__main__":
    main()
