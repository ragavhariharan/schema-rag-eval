"""
run_sql_agent_debug.py
═══════════════════════════════════════════════════════════════════════════════════
Interactive Debug Terminal for the Schema-RAG SQL Pipeline.

Runs the SAME code path as the API/agent (`pipeline.run_pipeline`) and shows its
internals for every query, so the trace always reflects real behavior — including
Phase 1 model-name routing and the alias/unit notes.

  ┌─ Stage 1: Routing → Retrieval → SQL Generation ──────────────┐
  │  Model-name routing or family/semantic? Which tables?        │
  │  Which alias/unit notes were injected? What SQL was made?    │
  ├─ Stage 2: Validation ────────────────────────────────────────┤
  │  Did the validator approve? Read-only / tables / columns?    │
  ├─ Stage 3: Execution ─────────────────────────────────────────┤
  │  Query results from Supabase                                 │
  └──────────────────────────────────────────────────────────────┘

Usage:
  python run_sql_agent_debug.py

Type 'exit' or 'quit' to close.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import time
import warnings

import chromadb
import pandas as pd

import pipeline
from pipeline import execute_sql_safely, CHROMA_DB_PATH, CHROMA_COLLECTION, OLLAMA_MODEL
from column_aliases import build_context_notes
from sql_validator import SQLValidator

warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
W = 88  # Terminal width

# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def hr(char="─"):
    return char * W

def stage_header(num, title, icon=""):
    print(f"\n  {icon} Stage {num}: {title}")
    print(f"  {hr()}")

def kv(key, value, indent=4):
    """Print a key-value pair with alignment."""
    spaces = " " * indent
    print(f"{spaces}{key:<22} {value}")

def print_products_table(products, max_rows=15):
    """Display products as a formatted table using pandas."""
    if not products:
        return
    df = pd.DataFrame(products[:max_rows])
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str[:45]
    print()
    print(df.to_string(index=False))
    if len(products) > max_rows:
        print(f"\n    ... and {len(products) - max_rows} more rows")


# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG PIPELINE — runs the real pipeline and exposes each stage
# ═══════════════════════════════════════════════════════════════════════════════

def run_debug_pipeline(user_query: str, collection, validator):
    """Run pipeline.run_pipeline() and show routing, generation, validation, and
    execution. Uses the production code path so the trace cannot drift."""

    t_total_start = time.time()

    # ── STAGE 1: ROUTING → RETRIEVAL → SQL GENERATION ─────────────────────
    # (run_pipeline may print "[Self-Healing]" lines here if it retries.)
    stage_header(1, "ROUTING → RETRIEVAL → SQL GENERATION", "🤖")
    t_start = time.time()
    clean_sql, contexts, filters = pipeline.run_pipeline(user_query)
    t_gen = time.time() - t_start

    # Routing mode
    resolved_models = filters.get("resolved_models")
    routed_tables = filters.get("routed_tables")
    if resolved_models:
        kv("Routing mode", "🎯 MODEL-NAME (Phase 1)")
        kv("Models matched", ", ".join(resolved_models))
    elif routed_tables:
        mode = "🧭 TABLE ROUTER (Phase 2)"
        if filters.get("cross_table"):
            mode += " — CROSS-TABLE"
        kv("Routing mode", mode)
        kv("Tables routed", ", ".join(routed_tables))
    else:
        active = {k: v for k, v in filters.items() if v}
        kv("Routing mode", "FAMILY / SEMANTIC (fallback)")
        kv("Filters", json.dumps(active) if active else "(none — pure semantic search)")

    # Which tables surfaced (parsed from chunk headers "[Table: <name>]")
    tables = []
    for c in contexts:
        m = re.search(r"\[Table:\s*([^\]]+)\]", c)
        if m:
            tables.append(m.group(1).strip())
    kv("Chunks retrieved", len(contexts))
    kv("Tables in context", ", ".join(tables) if tables else "(none)")

    # Alias / unit notes that were injected into the generation prompt
    notes = build_context_notes(tables)
    if notes.strip():
        print()
        print("    📐 Alias/unit notes injected into the prompt:")
        for line in notes.strip().split("\n"):
            print(f"       {line}")

    print()
    print("    ── Generated SQL ──")
    for line in clean_sql.strip().split("\n"):
        print(f"    {line}")
    print()
    kv("⏱  Time", f"{t_gen:.2f}s")

    # ── STAGE 2: VALIDATION ───────────────────────────────────────────────
    stage_header(2, "SQL VALIDATION", "🛡️")
    val_result = validator.validate(clean_sql)
    kv("Valid", "✅ Yes" if val_result.is_valid else "❌ No")
    kv("Read-only", "✅" if val_result.read_only else "❌")
    kv("Tables valid", "✅" if val_result.tables_valid else "❌")
    kv("Columns valid", "✅" if val_result.columns_valid else "❌")
    if not val_result.is_valid:
        kv("Reason", val_result.reason)

    # ── STAGE 3: EXECUTION ────────────────────────────────────────────────
    stage_header(3, "DATABASE EXECUTION", "🗄️")
    t_start = time.time()
    if not val_result.is_valid:
        print("    ⛔ Skipped — SQL failed validation.")
    else:
        df, error = execute_sql_safely(clean_sql)
        t_exec = time.time() - t_start
        if error:
            kv("Status", "❌ Execution Error")
            kv("Error", error[:200])
        elif df is None or df.empty:
            kv("Status", "⚠️  No Results")
            kv("Rows", 0)
        else:
            kv("Status", "✅ Success")
            kv("Rows returned", len(df))
            kv("Columns", ", ".join(df.columns.tolist()))
            print_products_table(df.to_dict(orient="records"))
        kv("⏱  Time", f"{t_exec:.2f}s")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    t_total = time.time() - t_total_start
    print(f"\n  {'═' * W}")
    print(f"  ⏱  Total pipeline time: {t_total:.2f}s")
    print(f"  {'═' * W}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * W}")
    print(f"  🔬 Schema-RAG Debug Terminal — Full Pipeline Observability")
    print(f"{'═' * W}")
    print(f"  Initializing...")

    # Load ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name=CHROMA_COLLECTION)
    print(f"  ✅ ChromaDB: {collection.count()} chunks indexed")

    # Load Validator
    validator = SQLValidator()
    print(f"  ✅ Validator: {len(validator.valid_tables)} tables loaded")

    # Load Schema Registry for summary
    registry_path = os.path.join(SCRIPT_DIR, "schema_registry.json")
    with open(registry_path, "r") as f:
        schema = json.load(f)
    print(f"  ✅ Schema Registry: {len(schema)} tables")

    # Model index status (Phase 1 routing is active only when this exists)
    model_idx = pipeline._load_model_index()
    if model_idx:
        print(f"  ✅ Model index: {len(model_idx)} model names (routing ON)")
    else:
        print(f"  ⚠️  Model index: NOT built — run build_model_index.py (model routing OFF)")

    print(f"  ✅ LLM (router/filter): {OLLAMA_MODEL}")
    print(f"  ✅ LLM (SQL generation): {pipeline.SQL_GEN_MODEL}")
    print()
    print(f"  Enter a natural language query to see the full pipeline trace.")
    print(f"  Type 'exit' to quit.")
    print(f"{'═' * W}")

    while True:
        try:
            user_input = input("\n❓ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input or user_input.lower() in ("exit", "quit"):
            print("  Goodbye!")
            break

        print(f"\n{'═' * W}")
        print(f"  Query: \"{user_input}\"")
        print(f"{'═' * W}")

        try:
            run_debug_pipeline(user_input, collection, validator)
        except Exception as e:
            print(f"\n  💥 Pipeline Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
