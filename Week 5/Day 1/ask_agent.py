import sys
from agent_foundations import Agent, client, MODEL, tools, tool_functions

def main():
    # Check if question was provided as command line argument
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        # Ask for input interactively
        question = input("What would you like to ask? ")
    
    # Create agent with verbose=False for cleaner output (optional)
    agent = Agent(
        client=client,
        model=MODEL,
        tools=tools,
        tool_functions=tool_functions,
        max_iterations=6,
        verbose=True  # Set to False if you want cleaner output
    )
    
    # Run the agent
    print("\n" + "-"*50)
    print("Processing your question...")
    print("-"*50)
    
    answer = agent.run(question)
    
    print("\n" + "="*50)
    print("Answer:", answer)
    print("="*50)

if __name__ == "__main__":
    main()