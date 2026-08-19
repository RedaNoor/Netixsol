"""
Interactive command-line chat with the AFL agent. Run: python run_chat.py
"""
from agent import build_conversational_agent
from grounding import ToolCallLogger, check_grounding

SESSION_ID = "cli-session"


def main():
    conv_agent = build_conversational_agent(verbose=False)
    print("AFL Assistant ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        logger = ToolCallLogger()
        result = conv_agent.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": SESSION_ID}, "callbacks": [logger]},
        )
        answer = result["output"]
        print(f"\nAssistant: {answer}\n")

        if logger.calls:
            report = check_grounding(answer, logger)
            if not report["fully_grounded"]:
                print(f"[grounding check] numbers not traced to a tool call: "
                      f"{report['numbers_not_found_in_tool_output']}\n")


if __name__ == "__main__":
    main()
