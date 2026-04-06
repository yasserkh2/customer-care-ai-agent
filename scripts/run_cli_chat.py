import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_runtime_config
from app.graph import build_graph
from app.graph.state import create_initial_state


def main() -> None:
    load_runtime_config(
        config_path=PROJECT_ROOT / "config.yml",
        env_path=PROJECT_ROOT / ".env",
    )
    graph = build_graph()
    state = create_initial_state("")
    print("Customer Care AI Agent starter CLI")
    print("Type 'exit' to quit.")

    while True:
        user_query = input("\nYou: ").strip()
        if user_query.lower() in {"exit", "quit"}:
            print("Bye.")
            break

        state = graph.invoke(
            {
                **state,
                "user_query": user_query,
                "final_response": "",
                "retrieved_context": [],
            }
        )
        print(f"Bot: {state.get('final_response', '')}")


if __name__ == "__main__":
    main()
