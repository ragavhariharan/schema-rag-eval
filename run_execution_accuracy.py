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
     ChromaDB retrieval → SQL generation)  [imported from pipeline.py]
  3. Connect to the Supabase PostgreSQL database (schema: ragav)
  4. Execute both generated and expected SQL
  5. Compare result sets (shape + values, whitespace-normalized)
  6. Classify failures and generate reports

Outputs:
  - execution_accuracy_report.csv   (full audit trail)
  - execution_failures_only.csv     (filtered to failures for triage)
  - Terminal dashboard with accuracy % and failure breakdown

NOTE: The runtime pipeline (DB execution, ChromaDB retrieval, SQL generation)
lives in pipeline.py and is imported below. This file contains only the
evaluation harness on top of it.
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os
import re
import time
import warnings
from collections import Counter
from datetime import datetime

import pandas as pd

# ── Core runtime pipeline (single source of truth) ──────────────────────────────
from pipeline import (
    DB_CONFIG,
    execute_sql_safely,
    get_db_connection,
    run_pipeline,
)

# Suppress pandas warning about psycopg2 not being a SQLAlchemy connection.
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION (eval-specific paths)
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GOLDEN_DATASET_PATH = os.path.join(SCRIPT_DIR, "golden_dataset.json")
REPORT_CSV_PATH = os.path.join(SCRIPT_DIR, "execution_accuracy_report.csv")
FAILURES_CSV_PATH = os.path.join(SCRIPT_DIR, "execution_failures_only.csv")


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

    # Single-column result sets (e.g. an aggregate like COUNT(*)): the column
    # name is an arbitrary alias, so compare by VALUE — align the one generated
    # column onto the expected name before the value check below.
    if len(df_expected.columns) == 1 and len(df_generated.columns) == 1:
        df_generated.columns = list(df_expected.columns)
        expected_cols = generated_cols = set(df_expected.columns)

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

def run_execution_accuracy(dataset_path=GOLDEN_DATASET_PATH):
    """Main entry point: run the full execution accuracy evaluation.

    dataset_path defaults to golden_dataset.json; pass another path (e.g.
    smart_eval_dataset.json) on the command line to evaluate a different suite.
    """

    # ── Load dataset ──────────────────────────────────────────────────────
    print(f"\n{'═' * TRACE_WIDTH}")
    print(f"  🚀  EXECUTION ACCURACY EVALUATION")
    print(f"  Loading dataset from: {dataset_path}")
    print(f"{'═' * TRACE_WIDTH}")

    with open(dataset_path, "r") as f:
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
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else GOLDEN_DATASET_PATH
    run_execution_accuracy(path)
