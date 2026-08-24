"""
Interactive command-line chat with the full LangGraph AFL application (routing, retrieval,
prediction, validation, clarification, all wired together). Run: python run_chat.py
"""
import uuid
from graph import build_graph

SESSION_ID = f"cli-{uuid.uuid4().hex[:8]}"


def main():
    app = build_graph()
    config = {"configurable": {"thread_id": SESSION_ID}}
    print("AFL Assistant (LangGraph) ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        result = app.invoke({"user_query": user_input}, config=config)
        print(f"\nAssistant [{result.get('intent', '?')}]: {result['final_response']}\n")


if __name__ == "__main__":
    main()
