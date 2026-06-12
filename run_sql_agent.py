"""
run_sql_agent.py
═══════════════════════════════════════════════════════════════════════════════════
Interactive Terminal Interface for the SQL Agent.

Supports Natural Language queries: e.g. "What 8K 5u lenses weigh under 200g?"

Type 'exit' or 'quit' to close.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import pandas as pd

from sql_agent import SQLAgent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
W = 70  # Terminal width


def create_empty_state(user_input: str = "") -> dict:
    """Create a minimal state dict with only the fields the SQL Agent uses."""
    return {
        "user_input": user_input,
        "products": [],
        "errors": [],
    }


def print_products_table(products: list, max_rows: int = 20):
    """Display products as a formatted table using pandas."""
    if not products:
        return
    df = pd.DataFrame(products[:max_rows])
    # Truncate long string columns for display
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str[:40]
    print(df.to_string(index=False))
    if len(products) > max_rows:
        print(f"  ... and {len(products) - max_rows} more rows")


def main():
    print(f"\n{'═' * W}")
    print(f"  🤖 SQL Agent Interactive Terminal")
    print(f"{'═' * W}")
    print(f"  Initializing agent...")

    agent = SQLAgent()

    # Load registry to get table count for terminal output
    registry_path = os.path.join(SCRIPT_DIR, "schema_registry.json")
    with open(registry_path, "r") as f:
        schema = json.load(f)

    print(f"  ✅ Schema loaded: {len(schema)} tables")
    print(f"  ✅ Validator ready")
    print()
    print(f"  Usage:")
    print(f"    Enter a Natural Language query. Example: What 8K 5u lenses weigh under 200g?")
    print(f"    Type 'exit' to quit.")
    print(f"{'═' * W}")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input or user_input.lower() in ("exit", "quit"):
            print("  Goodbye!")
            break

        # ── Setup state ───────────────────────────────────────────────────
        state = create_empty_state(user_input=user_input)

        # ── Execute ───────────────────────────────────────────────────────
        state = agent.execute(state)
        result = state.get("sql_agent_result", {})

        # ── Display results ───────────────────────────────────────────────
        print(f"  {'─' * (W - 4)}")

        if result.get("sql"):
            sql_lines = result["sql"].strip().split("\n")
            print(f"  SQL:        {sql_lines[0]}")
            for line in sql_lines[1:]:
                print(f"              {line}")

        status = result.get("status", "unknown")

        if status == "success":
            print(f"  Status:     ✅ Success ({result['count']} products)")
            print()
            print_products_table(result["products"])

        elif status == "no_results":
            print(f"  Status:     ⚠️  No Results")
            print(f"  No products matched the given constraints.")

        elif status == "error":
            print(f"  Status:     ❌ Error")
            print(f"  Type:       {result.get('error_type', 'unknown')}")
            print(f"  Message:    {result.get('message', '')}")

        # Show state errors if any
        if state.get("errors"):
            print(f"\n  State errors:")
            for e in state["errors"]:
                print(f"    [{e['source']}] {e['error_type']}: {e.get('message', '')}")

        print(f"  {'─' * (W - 4)}")


if __name__ == "__main__":
    main()
