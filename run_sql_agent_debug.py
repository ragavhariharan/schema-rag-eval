"""
run_sql_agent_debug.py
═══════════════════════════════════════════════════════════════════════════════════
Interactive Debug Terminal for the Schema-RAG SQL Pipeline.

Shows the FULL pipeline internals for every query:

  ┌─ Stage 1: Filter Extraction ─────────────────────────────────┐
  │  What did the LLM extract? (product_type, resolution, etc.)  │
  ├─ Stage 2: ChromaDB Retrieval ────────────────────────────────┤
  │  Which chunks were retrieved? Which tables? Distances?       │
  ├─ Stage 3: SQL Generation ────────────────────────────────────┤
  │  What SQL was generated? Did self-healing kick in?           │
  ├─ Stage 4: Validation ────────────────────────────────────────┤
  │  Did the validator approve? Which tables/columns?            │
  ├─ Stage 5: Execution ─────────────────────────────────────────┤
  │  Query results from Supabase                                 │
  └──────────────────────────────────────────────────────────────┘

Usage:
  python run_sql_agent_debug.py

Type 'exit' or 'quit' to close.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import time
import warnings

import chromadb
import pandas as pd

from pipeline import (
    llm_extract_filters,
    extract_sql_from_text,
    execute_sql_safely,
    CHROMA_DB_PATH,
    CHROMA_COLLECTION,
    OLLAMA_MODEL,
)
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
# DEBUG PIPELINE — exposes every stage
# ═══════════════════════════════════════════════════════════════════════════════

def run_debug_pipeline(user_query: str, collection, validator):
    """Run the full RAG pipeline with verbose debug output at every stage."""

    t_total_start = time.time()

    # ── STAGE 1: Filter Extraction ────────────────────────────────────────
    stage_header(1, "FILTER EXTRACTION", "🔍")
    t_start = time.time()
    filters = llm_extract_filters(user_query)
    t_filter = time.time() - t_start

    active_filters = {k: v for k, v in filters.items() if v is not None}
    if active_filters:
        for k, v in active_filters.items():
            kv(k, v)
    else:
        kv("(none)", "No metadata filters extracted — pure semantic search")
    kv("⏱  Time", f"{t_filter:.2f}s")

    # ── STAGE 2: ChromaDB Retrieval ───────────────────────────────────────
    stage_header(2, "CHROMADB RETRIEVAL", "📚")
    t_start = time.time()

    search_params = {"query_texts": [user_query], "n_results": 3}
    and_conditions = []
    if filters.get("product_type"):
        and_conditions.append({"product_type": filters["product_type"]})
    if filters.get("resolution_target"):
        and_conditions.append({"resolution_target": filters["resolution_target"]})
    if filters.get("pixel_pitch_um") is not None:
        and_conditions.append({"pixel_pitch_um": filters["pixel_pitch_um"]})
    if filters.get("is_coaxial") is True:
        and_conditions.append({"is_coaxial": True})
    if filters.get("is_new_series") is True:
        and_conditions.append({"is_new_series": True})

    if and_conditions:
        search_params["where"] = (
            {"$and": and_conditions} if len(and_conditions) > 1 else and_conditions[0]
        )

    results = collection.query(**search_params)
    contexts = results["documents"][0] if results["documents"] else []
    t_retrieval = time.time() - t_start

    kv("Chunks retrieved", len(contexts))
    kv("ChromaDB filter", json.dumps(search_params.get("where", "(none)")))

    if results["ids"][0]:
        print()
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            distance = results["distances"][0][i]
            meta = results["metadatas"][0][i]
            table = meta.get("table_name", "?")
            ptype = meta.get("product_type", "?")
            # Show first 80 chars of chunk text
            snippet = results["documents"][0][i][:100].replace("\n", " ")
            print(f"    Hit {i+1}  │ dist={distance:.4f}  │ table={table}  │ type={ptype}")
            print(f"           │ {snippet}...")
    else:
        print("    ⚠️  No chunks retrieved! The query may not match any product family.")

    kv("⏱  Time", f"{t_retrieval:.2f}s")

    # ── STAGE 3: SQL Generation ───────────────────────────────────────────
    stage_header(3, "SQL GENERATION (LLM)", "🤖")
    t_start = time.time()

    import ollama

    system_prompt = f"""You are an expert PostgreSQL engineer for an industrial machine vision company.
Your job is to convert the user's request into a flawless SQL query.

RULES:
1. Base your query ONLY on the provided SCHEMA CONTEXT.
2. Do not hallucinate column names.
3. Output ONLY the raw SQL code. Do not include markdown formatting, explanations, or pleasantries.
4. Always include model_name in the SELECT clause.
5. SELECT only the columns that are directly relevant to the user's question. Do not add extra columns.

SUPERLATIVE QUERIES:
When a user asks for a "maximum", "minimum", "fastest", "cheapest", or "costliest" lens, they want the specific lens model record, not an isolated aggregate number.
CRITICAL: Since columns like list_price, weight_g, etc., can contain NULL values, you MUST filter them out so NULLs are not sorted first.
Example: "What is the fastest lens?" -> SELECT model_name, f_no_min FROM [table] WHERE f_no_min IS NOT NULL ORDER BY f_no_min ASC LIMIT 1;
Example: "What is the cheapest lens?" -> SELECT model_name, list_price FROM [table] WHERE list_price IS NOT NULL ORDER BY list_price ASC LIMIT 1;
Example: "What is the costliest lens?" -> SELECT model_name, list_price FROM [table] WHERE list_price IS NOT NULL ORDER BY list_price DESC LIMIT 1;

ENGINEERING GLOSSARY (apply these mappings EXACTLY in every query):
- "Maximum Aperture", "Widest Aperture", or "Fastest Lens" ALWAYS maps to the `f_no_min` column (lower f-number = wider aperture).
- "Minimum Aperture" or "stopped down the most" ALWAYS maps to the `f_no_max` column (higher f-number = smaller aperture). Use ORDER BY f_no_max DESC LIMIT 1 to find the lens that stops down the most.
- "Warping" or "distortion" maps to `tv_distortion_percent`.
- "Edge brightness", "relative illuminance", or "uniformity" maps to `relative_illuminance_percent`.
- "Standoff" or "working distance" maps to `wd_mm`. NOTE: Some tables use `wd_min_mm` and `wd_max_mm` for a working distance range instead of a single `wd_mm`. Check the SCHEMA CONTEXT to determine which columns are available.
- "Total conjugate distance" maps to `o_i`.
- "Telecentricity" maps to `telecentricity_degrees`.
- "Depth of field" or "DOF" maps to `dof_mm`.
- "Numerical aperture" or "NA" maps to `numerical_aperture` (or `numerical_aperture_min`/`numerical_aperture_max` for ranges).
- "Sensor format" or "sensor size" maps to `sensor_size_raw`.
- "Megapixel" or "MP" maps to `megapixel_rating`.
- "MOD" or "minimum object distance" maps to `mod_distance_m` (in meters).
- "Zoom type" maps to `zoom_type` (manual / motorized).
- "Wavelength" maps to `wavelength_min_nm` / `wavelength_max_nm` or `wavelength_raw`.
- "Response time" maps to `response_time_ms`.
- "Adapter" or "mount conversion" — check `mount_primary_raw` and `mount_secondary_raw` in adapter/ring tables.

CROSS-TABLE QUERIES:
If the user asks a general question comparing across all lenses without specifying a specific product family, you MUST query across all relevant tables.
- Use `UNION ALL` to combine results from all tables in the SCHEMA CONTEXT that contain the requested columns.
- DO NOT just query a single table. Ensure you include EVERY relevant table from the context.
- CRITICAL SYNTAX RULE: Do NOT place semicolons (;) at the end of the individual SELECT statements within a UNION ALL. Only place a single semicolon at the very end of the final query.

SCHEMA CONTEXT:
{chr(10).join(contexts)}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    max_retries = 2
    attempts = 0
    clean_sql = ""

    while attempts <= max_retries:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0, "num_ctx": 8192},
        )
        raw_response = response["message"]["content"]
        clean_sql = extract_sql_from_text(raw_response)

        val_result = validator.validate(clean_sql)
        if val_result.is_valid:
            break

        attempts += 1
        if attempts <= max_retries:
            correction_prompt = (
                f"The SQL you generated failed validation.\n"
                f"Bad SQL:\n{clean_sql}\n"
                f"Validation Error: {val_result.reason}\n"
                f"Please fix the error and output only the corrected raw SQL based strictly on the SCHEMA CONTEXT."
            )
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": correction_prompt})
            print(f"    ⚠️  Self-Healing Attempt {attempts}/{max_retries}: {val_result.reason}")

    t_gen = time.time() - t_start

    print()
    for line in clean_sql.strip().split("\n"):
        print(f"    {line}")
    print()
    kv("Self-heal attempts", attempts)
    kv("⏱  Time", f"{t_gen:.2f}s")

    # ── STAGE 4: Validation ───────────────────────────────────────────────
    stage_header(4, "SQL VALIDATION", "🛡️")
    val_result = validator.validate(clean_sql)

    kv("Valid", "✅ Yes" if val_result.is_valid else "❌ No")
    kv("Read-only", "✅" if val_result.read_only else "❌")
    kv("Tables valid", "✅" if val_result.tables_valid else "❌")
    kv("Columns valid", "✅" if val_result.columns_valid else "❌")
    if not val_result.is_valid:
        kv("Reason", val_result.reason)

    # ── STAGE 5: Execution ────────────────────────────────────────────────
    stage_header(5, "DATABASE EXECUTION", "🗄️")
    t_start = time.time()

    if not val_result.is_valid:
        print("    ⛔ Skipped — SQL failed validation.")
        return

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
        products = df.to_dict(orient="records")
        print_products_table(products)

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

    print(f"  ✅ LLM: {OLLAMA_MODEL}")
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
