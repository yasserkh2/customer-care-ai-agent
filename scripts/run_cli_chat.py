from app.graph import build_graph
from app.graph.state import create_initial_state


def main() -> None:
    graph = build_graph()
    print("Customer Care AI Agent starter CLI")
    print("Type 'exit' to quit.")

    while True:
        user_query = input("\nYou: ").strip()
        if user_query.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        result = graph.invoke(create_initial_state(user_query))
        print(f"Bot: {result.get('final_response', '')}")


if __name__ == "__main__":
    main()
