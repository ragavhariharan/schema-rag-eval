"""
run_execution_accuracy.py
═════════════════════════════════════════════════════════════════════════════════
Execution Accuracy Evaluation for the EarthTekniks Text-to-SQL Pipeline.

Instead of LLM-graded language metrics, this script measures result-set
equivalence: Does the generated SQL yield the exact same dataset as the
ground-truth SQL when both are executed against the live database?

Pipeline:
  1. Load golden_dataset.json
  2. For each question, run the unified RAG pipeline (filter extraction →
     ChromaDB retrieval → SQL generation)
  3. Connect to the Supabase PostgreSQL database (schema: ragav)
  4. Execute both generated and expected SQL
  5. Compare result sets (shape + values, whitespace-normalized)
  6. Classify failures and generate reports

Outputs:
  - execution_accuracy_report.csv   (full audit trail)
  - execution_failures_only.csv     (filtered to failures for triage)
  - Terminal dashboard with accuracy % and failure breakdown
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os
import re
import time
import traceback
import warnings
from collections import Counter
from datetime import datetime

import chromadb
import ollama
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Suppress pandas warning about psycopg2 not being a SQLAlchemy connection.
# We intentionally use psycopg2 directly for lightweight read-only queries.
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=True)

GOLDEN_DATASET_PATH = os.path.join(SCRIPT_DIR, "golden_dataset.json")
REPORT_CSV_PATH = os.path.join(SCRIPT_DIR, "execution_accuracy_report.csv")
FAILURES_CSV_PATH = os.path.join(SCRIPT_DIR, "execution_failures_only.csv")
OLLAMA_MODEL = "qwen2.5-coder"
CHROMA_DB_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
CHROMA_COLLECTION = "lens_schema_rag"

# Database connection parameters — pulled from individual .env variables
# to avoid URL-parsing issues with special characters in the password.
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "6543"),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "options": "-c search_path=ragav",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_db_connection():
    """Establish a secure psycopg2 connection to the Supabase PostgreSQL
    database, scoped to the 'ragav' schema via connection-level options."""
    missing = [k for k in ("host", "user", "password") if not DB_CONFIG.get(k)]
    if missing:
        raise ValueError(
            f"Missing required DB env vars: {', '.join('DB_' + k.upper() for k in missing)}. "
            "Check your .env file."
        )

    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        options=DB_CONFIG["options"],
        connect_timeout=15,
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn

def execute_sql_safely(sql: str) -> tuple:
    """Open a fresh DB connection, execute a SQL query, close it, and return
    (dataframe, error_string).

    A fresh connection per query avoids the Supabase pooler killing idle
    connections while the LLM pipeline is thinking between queries.

    Returns:
        (pd.DataFrame, None)  on success
        (None, str)           on failure (error message)
    """
    conn = None
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: RAG PIPELINE (reused from run_ragas.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_collection(name=CHROMA_COLLECTION)


def llm_extract_filters(user_query: str) -> dict:
    """Dynamically extract ChromaDB metadata filters from a user query using the LLM.

    Uses Ollama's JSON mode for structured output. Returns a dict with keys
    matching ChromaDB metadata fields. Values are None for unidentified filters.
    """
    system_prompt = """You are a metadata filter extractor for a line scan lens catalog database.
Given a user's natural language query about lenses, extract the following metadata filters as JSON:

{
  "resolution_target": string or null (e.g. "4K", "8K", "12K", "16K" — extracted from mentions like "8K", "12k", "12K"),
  "pixel_pitch_um": number or null (e.g. 5.0, 7.0, 3.5 — extracted from mentions like "5u", "5µm", "5 micron", "3.5u"),
  "is_coaxial": true/false or null (true ONLY if the query explicitly mentions "coaxial"),
  "is_new_series": true/false or null (true ONLY if the query explicitly mentions "new series")
}

RULES:
- Return ONLY the JSON object, nothing else.
- Use null for any filter you cannot confidently extract from the query.
- "resolution_target" must always be uppercase with K suffix (e.g. "8K", not "8k").
- "pixel_pitch_um" must be a number (e.g. 3.5, not "3.5u").
- If the query mentions no specific resolution, pixel pitch, coaxial, or new series, return all nulls.
- Queries about general lens properties (e.g. "all lenses under 200g") should return all nulls."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        format="json",
        options={"temperature": 0, "num_ctx": 8192},
    )

    try:
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError):
        return {"resolution_target": None, "pixel_pitch_um": None, "is_coaxial": None, "is_new_series": None}

    filters = {
        "resolution_target": None,
        "pixel_pitch_um": None,
        "is_coaxial": None,
        "is_new_series": None,
    }

    if parsed.get("resolution_target") and isinstance(parsed["resolution_target"], str):
        val = parsed["resolution_target"].upper().replace(" ", "")
        if not val.endswith("K"):
            val += "K"
        filters["resolution_target"] = val

    if parsed.get("pixel_pitch_um") is not None:
        try:
            filters["pixel_pitch_um"] = float(parsed["pixel_pitch_um"])
        except (ValueError, TypeError):
            pass

    if isinstance(parsed.get("is_coaxial"), bool):
        filters["is_coaxial"] = parsed["is_coaxial"]

    if isinstance(parsed.get("is_new_series"), bool):
        filters["is_new_series"] = parsed["is_new_series"]

    return filters


def extract_sql_from_text(text: str) -> str:
    """Extract clean SQL from an LLM response that may contain markdown fences."""
    sql_match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
    generic_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()
    return text.strip()


def run_pipeline(user_query: str) -> tuple:
    """Run the full RAG pipeline: extract filters → retrieve chunks → generate SQL.
    Includes an SQL Safety Layer with a self-healing retry loop.

    Returns:
        (generated_sql, retrieved_contexts, extracted_filters)
    """
    filters = llm_extract_filters(user_query)

    search_params = {"query_texts": [user_query], "n_results": 5}

    and_conditions = []
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
- "Edge brightness", "relative illuminance", or "uniformity" maps to `relative_illuminance_percent`. NOTE: Percentages are stored as whole numbers (e.g., 75% is 75). If a user queries > X%, you MUST include the exact value if the companion operator is '>' or '>='. For example, use: `(relative_illuminance_percent > X OR (relative_illuminance_percent = X AND relative_illuminance_operator IN ('>', '>=')))`.
- "Standoff" or "working distance" maps to `wd_mm`.
- "Total conjugate distance" maps to `o_i`.

CROSS-TABLE QUERIES:
If the user asks a general question comparing across all lenses without specifying a specific resolution/pitch target, you MUST query across all relevant tables.
- Use `UNION ALL` to combine results from all tables in the SCHEMA CONTEXT that contain the requested columns.
- DO NOT just query a single table. Ensure you include EVERY relevant table from the context.
- CRITICAL SYNTAX RULE: Do NOT place semicolons (;) at the end of the individual SELECT statements within a UNION ALL. Only place a single semicolon at the very end of the final query.

SCHEMA CONTEXT:
{chr(10).join(contexts)}"""

    # Lazy instantiate the validator to prevent disk I/O overhead on every loop iteration
    global _validator
    if '_validator' not in globals() or _validator is None:
        from sql_validator import SQLValidator
        _validator = SQLValidator()

    # --------------------------------------------------------------------------
    # SELF-HEALING RETRY LOOP
    # --------------------------------------------------------------------------
    # 1. We allow an initial generation attempt plus up to 2 retries (total 3 tries).
    # 2. On failure, we append the bad SQL and the validator's failure reason to the 
    #    message history and ask the LLM to correct its mistake.
    # 3. If validation passes, we break the loop and return the SQL immediately.
    # 4. If we hit the retry limit and still fail, we return the last bad SQL so the
    #    main execution pipeline can log the failure appropriately.
    # --------------------------------------------------------------------------
    
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

        # Validate the generated SQL
        val_result = _validator.validate(clean_sql)
        if val_result.is_valid:
            # SQL is structurally sound and schema-compliant
            break
            
        attempts += 1
        if attempts <= max_retries:
            # Self-Heal: Append the failure context as a new user message prompting correction
            correction_prompt = (
                f"The SQL you generated failed validation.\n"
                f"Bad SQL:\n{clean_sql}\n"
                f"Validation Error: {val_result.reason}\n"
                f"Please fix the error and output only the corrected raw SQL based strictly on the SCHEMA CONTEXT."
            )
            # Add the model's bad response and the user's correction instruction to the conversation
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": correction_prompt})
            print(f"  [Self-Healing] Attempt {attempts}/{max_retries}. Reason: {val_result.reason}")

    return clean_sql, contexts, filters


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: RESULT-SET COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a DataFrame for comparison: strip whitespace from strings,
    sort columns alphabetically, sort rows, and reset index."""
    df = df.copy()

    # Normalize string columns: strip whitespace
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().str.lower()

    # Sort columns alphabetically for structural comparison
    df = df.reindex(sorted(df.columns), axis=1)

    # Sort rows by all columns to make row order irrelevant
    df = df.sort_values(by=list(df.columns)).reset_index(drop=True)

    return df


def compare_result_sets(df_expected: pd.DataFrame, df_generated: pd.DataFrame) -> bool:
    """Compare two DataFrames for result-set equivalence.

    Returns True if the generated result matches the expected data.
    Handles two scenarios:
      1. Exact match — identical columns and values.
      2. Column superset — generated has all expected columns plus extras.
         Only the expected columns are compared (extras ignored).

    Missing required columns (generated is a subset of expected) is a
    hard failure — the AI must return at least the expected columns.

    In both cases, row ordering, whitespace, and string casing are ignored.
    """
    # Lowercase column names for case-insensitive matching
    df_expected = df_expected.copy()
    df_generated = df_generated.copy()
    df_expected.columns = [c.lower().strip() for c in df_expected.columns]
    df_generated.columns = [c.lower().strip() for c in df_generated.columns]

    expected_cols = set(df_expected.columns)
    generated_cols = set(df_generated.columns)

    if expected_cols == generated_cols:
        # Exact column match — compare everything
        pass
    elif expected_cols.issubset(generated_cols):
        # Generated has all expected columns + extras.
        # Trim generated down to only the expected columns before comparing.
        df_generated = df_generated[list(df_expected.columns)]
    else:
        # Generated is missing one or more expected columns — hard fail
        return False

    # Row count check
    if len(df_expected) != len(df_generated):
        return False

    norm_expected = normalize_dataframe(df_expected)
    norm_generated = normalize_dataframe(df_generated)

    # Value check
    try:
        return norm_expected.equals(norm_generated)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: FAILURE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def classify_failure(
    generated_sql: str,
    expected_sql: str,
    gen_error: str | None,
    exp_error: str | None,
    df_generated: pd.DataFrame | None,
    df_expected: pd.DataFrame | None,
) -> str:
    """Classify a failure into one of the predefined diagnostic categories.

    Categories:
        invalid_sql        – Syntax errors, connection timeouts, or execution crashes
        wrong_table        – Generated SQL targets a different table than expected
        wrong_filter       – WHERE clause filters don't match
        wrong_sort         – ORDER BY / LIMIT differences
        wrong_aggregation  – Aggregate function mismatches (COUNT, SUM, AVG, etc.)
        result_mismatch    – Both executed successfully but data doesn't match
    """
    # If the generated SQL itself crashed, it's invalid SQL
    if gen_error is not None:
        return "invalid_sql"

    # If the expected SQL crashed (shouldn't happen, but defensive)
    if exp_error is not None:
        return "invalid_sql"

    gen_upper = generated_sql.upper()
    exp_upper = expected_sql.upper()

    # --- Table Detection ---
    # Extract table names from FROM clauses
    gen_tables = set(re.findall(r"FROM\s+(\w+)", gen_upper))
    exp_tables = set(re.findall(r"FROM\s+(\w+)", exp_upper))
    if gen_tables != exp_tables:
        return "wrong_table"

    # --- Aggregation Detection ---
    agg_funcs = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
    gen_has_agg = any(f"{fn}(" in gen_upper for fn in agg_funcs)
    exp_has_agg = any(f"{fn}(" in exp_upper for fn in agg_funcs)
    if gen_has_agg != exp_has_agg:
        return "wrong_aggregation"

    # --- Sort Detection ---
    gen_has_order = "ORDER BY" in gen_upper
    exp_has_order = "ORDER BY" in exp_upper
    gen_has_limit = "LIMIT" in gen_upper
    exp_has_limit = "LIMIT" in exp_upper
    if gen_has_order != exp_has_order or gen_has_limit != exp_has_limit:
        return "wrong_sort"
    # If both have ORDER BY, check if the sort columns/direction differ
    if gen_has_order and exp_has_order:
        gen_order = re.search(r"ORDER BY\s+(.+?)(?:LIMIT|$)", gen_upper, re.DOTALL)
        exp_order = re.search(r"ORDER BY\s+(.+?)(?:LIMIT|$)", exp_upper, re.DOTALL)
        if gen_order and exp_order:
            gen_sort_str = re.sub(r"\s+", " ", gen_order.group(1).strip())
            exp_sort_str = re.sub(r"\s+", " ", exp_order.group(1).strip())
            if gen_sort_str != exp_sort_str:
                return "wrong_sort"

    # --- Filter Detection ---
    gen_has_where = "WHERE" in gen_upper
    exp_has_where = "WHERE" in exp_upper
    if gen_has_where != exp_has_where:
        return "wrong_filter"
    if gen_has_where and exp_has_where:
        gen_where = re.search(r"WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)", gen_upper, re.DOTALL)
        exp_where = re.search(r"WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)", exp_upper, re.DOTALL)
        if gen_where and exp_where:
            gen_filter_str = re.sub(r"\s+", " ", gen_where.group(1).strip())
            exp_filter_str = re.sub(r"\s+", " ", exp_where.group(1).strip())
            if gen_filter_str != exp_filter_str:
                return "wrong_filter"

    # --- Catch-all: data simply doesn't match ---
    return "result_mismatch"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: TERMINAL UI — OBSERVABILITY TRACE
# ═══════════════════════════════════════════════════════════════════════════════

TRACE_WIDTH = 88

def _hr(char="═"):
    return char * TRACE_WIDTH


def _print_boxed(label: str, content: str, icon: str = ""):
    """Print a labeled section inside the trace."""
    prefix = f"  {icon} " if icon else "  "
    print(f"{prefix}{label}")
    for line in content.strip().split("\n"):
        print(f"     {line}")


def print_query_trace(idx: int, total: int, item: dict, generated_sql: str,
                      filters: dict, match: bool, failure_tag: str | None,
                      elapsed: float, gen_error: str | None):
    """Print a rich terminal trace for a single evaluation."""
    status_icon = "✅" if match else "❌"
    status_text = "PASS" if match else f"FAIL → {failure_tag}"

    print(f"\n{'─' * TRACE_WIDTH}")
    print(f"  [{idx}/{total}]  {item['id']}")
    print(f"  ❓ {item['question']}")
    print(f"  {'─' * (TRACE_WIDTH - 4)}")

    # Filters
    active = {k: v for k, v in filters.items() if v is not None}
    filter_str = json.dumps(active) if active else "(none — semantic search only)"
    print(f"  🔍 Filters: {filter_str}")

    # SQLs side by side
    print(f"  📋 Expected SQL:")
    print(f"       {item['expected_sql']}")
    print(f"  🤖 Generated SQL:")
    print(f"       {generated_sql}")

    if gen_error:
        print(f"  💥 Execution Error:")
        print(f"       {gen_error[:200]}")

    print(f"  {status_icon} Result: {status_text}  ({elapsed:.2f}s)")


def print_dashboard(results: list[dict]):
    """Print the final evaluation dashboard to the terminal."""
    total = len(results)
    passed = sum(1 for r in results if r["match"])
    failed = total - passed
    accuracy = (passed / total * 100) if total > 0 else 0.0

    # Failure breakdown
    failure_tags = [r["failure_category"] for r in results if not r["match"]]
    tag_counts = Counter(failure_tags)

    print(f"\n{'═' * TRACE_WIDTH}")
    print(f"  📊  EXECUTION ACCURACY DASHBOARD")
    print(f"{'═' * TRACE_WIDTH}")
    print(f"  Timestamp        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total Queries    : {total}")
    print(f"  Passed (Match)   : {passed}")
    print(f"  Failed (Mismatch): {failed}")
    print(f"{'─' * TRACE_WIDTH}")

    # Accuracy bar
    bar_len = 40
    filled = int(bar_len * accuracy / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"  Accuracy: [{bar}] {accuracy:.1f}%")
    print(f"{'─' * TRACE_WIDTH}")

    if tag_counts:
        print(f"  🏷️  Failure Breakdown:")
        max_label_len = max(len(t) for t in tag_counts)
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            tag_bar = "▓" * int(20 * count / total)
            print(f"    {tag:<{max_label_len}}  {count:>3}  ({pct:>5.1f}%)  {tag_bar}")
    else:
        print(f"  🎉 No failures! Perfect execution accuracy.")

    print(f"{'═' * TRACE_WIDTH}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MAIN EVALUATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_execution_accuracy():
    """Main entry point: run the full execution accuracy evaluation."""

    # ── Load golden dataset ───────────────────────────────────────────────
    print(f"\n{'═' * TRACE_WIDTH}")
    print(f"  🚀  EXECUTION ACCURACY EVALUATION")
    print(f"  Loading golden dataset from: {GOLDEN_DATASET_PATH}")
    print(f"{'═' * TRACE_WIDTH}")

    with open(GOLDEN_DATASET_PATH, "r") as f:
        dataset = json.load(f)

    total = len(dataset)
    print(f"  📦 Loaded {total} evaluation queries.\n")

    # ── Verify database connectivity ──────────────────────────────────────
    print(f"  🔌 Connecting to Supabase PostgreSQL...")
    print(f"     Host   : {DB_CONFIG['host']}")
    print(f"     Port   : {DB_CONFIG['port']}")
    print(f"     DB     : {DB_CONFIG['dbname']}")
    print(f"     User   : {DB_CONFIG['user']}")
    print(f"     Schema : ragav (via search_path)")

    try:
        test_conn = get_db_connection()
        test_conn.close()
        print(f"  ✅ Connection verified (per-query pooling active).\n")
    except Exception as e:
        print(f"  ❌ FATAL: Could not connect to database.")
        print(f"     {e}")
        print(f"     Ensure .env variables are set correctly and the DB is reachable.")
        return

    # ── Evaluation loop ───────────────────────────────────────────────────
    # NOTE: Each SQL execution opens its own fresh connection to avoid
    # Supabase pooler idle-timeout killing the connection while the
    # LLM pipeline is thinking (20-70s per query).
    results = []

    for idx, item in enumerate(dataset, 1):
        t_start = time.time()

        # Step 1: Run the RAG pipeline to generate SQL
        try:
            generated_sql, contexts, filters = run_pipeline(item["question"])
        except Exception as e:
            generated_sql = f"PIPELINE_ERROR: {e}"
            contexts = []
            filters = {}

        # Step 2: Execute expected SQL (fresh connection)
        df_expected, exp_error = execute_sql_safely(item["expected_sql"])

        # Step 3: Execute generated SQL (fresh connection)
        df_generated, gen_error = execute_sql_safely(generated_sql)

        # Step 4: Compare result sets
        match = False
        failure_tag = None

        if df_expected is not None and df_generated is not None:
            match = compare_result_sets(df_expected, df_generated)

        if not match:
            failure_tag = classify_failure(
                generated_sql=generated_sql,
                expected_sql=item["expected_sql"],
                gen_error=gen_error,
                exp_error=exp_error,
                df_generated=df_generated,
                df_expected=df_expected,
            )

        elapsed = time.time() - t_start

        # Step 5: Record result
        active_filters = {k: v for k, v in filters.items() if v is not None} if filters else {}
        result_row = {
            "id": item["id"],
            "question": item["question"],
            "focus": item.get("focus", ""),
            "expected_sql": item["expected_sql"],
            "generated_sql": generated_sql,
            "filters_extracted": json.dumps(active_filters),
            "num_chunks_retrieved": len(contexts),
            "match": match,
            "failure_category": failure_tag if failure_tag else "",
            "gen_execution_error": gen_error if gen_error else "",
            "exp_execution_error": exp_error if exp_error else "",
            "expected_rows": len(df_expected) if df_expected is not None else -1,
            "generated_rows": len(df_generated) if df_generated is not None else -1,
            "elapsed_seconds": round(elapsed, 2),
        }
        results.append(result_row)

        # Step 6: Print trace
        print_query_trace(idx, total, item, generated_sql, filters, match, failure_tag, elapsed, gen_error)

    # ── Generate CSV reports ──────────────────────────────────────────────
    df_report = pd.DataFrame(results)

    df_report.to_csv(REPORT_CSV_PATH, index=False)
    print(f"  📁 Full report saved to: {REPORT_CSV_PATH}")

    df_failures = df_report[df_report["match"] == False].copy()
    df_failures.to_csv(FAILURES_CSV_PATH, index=False)
    print(f"  📁 Failures report saved to: {FAILURES_CSV_PATH}")

    # ── Print dashboard ───────────────────────────────────────────────────
    print_dashboard(results)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_execution_accuracy()
