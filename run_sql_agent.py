"""
run_sql_agent.py
═══════════════════════════════════════════════════════════════════════════════════
Interactive Terminal Interface for the SQL Agent.

Supports two input modes:
  1. Natural Language  → "What 8K 5u lenses weigh under 200g?"
  2. Structured Filters → {"table": "line_scan_lens_8k5u", "weight_g": {"$lt": 200}}

Type 'exit' or 'quit' to close.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json

import pandas as pd

from sql_agent import SQLAgent

W = 70  # Terminal width


def create_empty_state(user_input: str = "", filters: dict = None) -> dict:
    """Create a minimal state dict with only the fields the SQL Agent uses."""
    return {
        "user_input": user_input,
        "filters": filters or {},
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

    print(f"  ✅ Schema loaded: {len(agent.valid_tables)} tables")
    print(f"  ✅ Validator ready")
    print()
    print(f"  Input modes:")
    print(f"    Natural Language : What 8K 5u lenses weigh under 200g?")
    print(f"    Structured JSON  : {{\"table\": \"line_scan_lens_8k5u\", \"weight_g\": {{\"$lt\": 200}}}}")
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

        # ── Detect input mode ─────────────────────────────────────────────
        mode = "Natural Language"
        state = None

        try:
            parsed = json.loads(user_input)
            if isinstance(parsed, dict):
                state = create_empty_state(filters=parsed)
                mode = "Structured Filters"
        except (json.JSONDecodeError, ValueError):
            pass

        if state is None:
            state = create_empty_state(user_input=user_input)

        # ── Execute ───────────────────────────────────────────────────────
        state = agent.execute(state)
        result = state.get("sql_agent_result", {})

        # ── Display results ───────────────────────────────────────────────
        print(f"  {'─' * (W - 4)}")
        print(f"  Mode:       {mode}")

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
