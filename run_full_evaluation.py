"""
run_full_evaluation.py
═══════════════════════════════════════════════════════════════════════════════════
Unified Text-to-SQL Evaluation Pipeline for the EarthTekniks Lens Catalog.

Single entry point for all evaluation. No Ragas dependency.

Phases:
  1. SQL Generation + Safety Layer Metrics (uses existing pipeline)
  2. Execution Accuracy (DB comparison using proven logic)
  3. AST Diagnostics (deterministic sqlglot structural analysis)
  4. Pattern Accuracy (dynamic from dataset)
  5. Safety Layer Analytics
  6. Report Generation (CSV + Terminal Dashboard)

Dependencies: pandas, psycopg2, sqlglot, ollama
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import math
import os
import time
from collections import defaultdict

import pandas as pd
import sqlglot
from sqlglot import exp

# Import proven pipeline components — generation logic, DB execution, and validator
from run_execution_accuracy import run_pipeline, execute_sql_safely
from sql_validator import SQLValidator

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "evaluation_dataset.json")
REPORT_CSV_PATH = os.path.join(SCRIPT_DIR, "evaluation_report.csv")

W = 80  # Terminal dashboard width


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: SAFETY LAYER METRICS CAPTURE
# ═══════════════════════════════════════════════════════════════════════════════
# We intercept SQLValidator.validate() at the class level to capture every
# validation call made during run_pipeline()'s self-healing loop.  This lets
# us record safety metrics (triggered, retries, final status) without modifying
# the pipeline's generation or validation behavior in any way.

def run_pipeline_with_safety_metrics(question: str) -> tuple:
    """Wrap run_pipeline() to transparently capture safety layer metrics.

    Returns:
        (generated_sql, contexts, filters, safety_metrics_dict)
    """
    attempt_log = []
    original_validate = SQLValidator.validate

    # Intercept every call to validate() and record the result
    def intercepting_validate(self, sql):
        result = original_validate(self, sql)
        attempt_log.append({"sql": sql, "result": result})
        return result

    SQLValidator.validate = intercepting_validate
    try:
        gen_sql, contexts, filters = run_pipeline(question)
    finally:
        # Always restore the original method, even if the pipeline crashes
        SQLValidator.validate = original_validate

    # Derive safety metrics from the intercept log
    if not attempt_log:
        return gen_sql, contexts, filters, {
            "safety_triggered": False,
            "self_heal_attempts": 0,
            "validation_status": "No validation performed",
        }

    first_valid = attempt_log[0]["result"].is_valid
    last_valid = attempt_log[-1]["result"].is_valid
    safety_triggered = not first_valid
    # self_heal_attempts = number of retries AFTER the initial attempt
    self_heal_attempts = len(attempt_log) - 1 if safety_triggered else 0
    validation_status = attempt_log[-1]["result"].reason

    return gen_sql, contexts, filters, {
        "safety_triggered": safety_triggered,
        "self_heal_attempts": self_heal_attempts,
        "validation_status": validation_status,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: RESULT-SET COMPARISON (proven logic, unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
# This is the battle-tested comparison function from the advanced eval script.
# It implements:
#   Rule 1 — Scalar vs. Row handler (MIN/MAX vs LIMIT 1)
#   Rule 2 — Column-Name Agnostic Superset matching (UNION/alias mismatch)
#   Fallback — Exact pandas assert_frame_equal

def _safe_float(val):
    """Attempt to convert a value to float for numeric comparison."""
    try:
        if pd.isna(val):
            return val
        return float(val)
    except (ValueError, TypeError):
        return val


def _arrays_match(arr1, arr2) -> bool:
    """Check if two arrays are element-wise equal with numeric tolerance."""
    if len(arr1) != len(arr2):
        return False
    for a, b in zip(arr1, arr2):
        fa, fb = _safe_float(a), _safe_float(b)
        if isinstance(fa, float) and isinstance(fb, float):
            if not pd.isna(fa) and not pd.isna(fb):
                if not math.isclose(fa, fb, rel_tol=1e-5):
                    return False
            elif pd.isna(fa) and pd.isna(fb):
                continue
            else:
                return False
        else:
            if str(a) != str(b):
                return False
    return True


def compare_result_sets(df_expected: pd.DataFrame, df_generated: pd.DataFrame) -> tuple:
    """Compare expected and generated DataFrames for result-set equivalence.

    Returns:
        (bool, str) — (pass/fail, reason)
    """
    if df_expected.empty and df_generated.empty:
        return True, "Both sets empty (Pass)"
    if df_expected.empty or df_generated.empty:
        return False, "One set empty, other not"

    # Sort rows for order-independent comparison
    if len(df_expected) > 1:
        df_expected = df_expected.sort_values(by=list(df_expected.columns)).reset_index(drop=True)
    if len(df_generated) > 1:
        df_generated = df_generated.sort_values(by=list(df_generated.columns)).reset_index(drop=True)

    # Rule 1: Scalar vs. Row — expected is 1x1, generated is 1xN
    if df_expected.shape == (1, 1) and len(df_generated) == 1:
        expected_scalar = df_expected.iloc[0, 0]
        f_exp = _safe_float(expected_scalar)
        for val in df_generated.iloc[0].values:
            f_val = _safe_float(val)
            if isinstance(f_exp, float) and isinstance(f_val, float):
                if math.isclose(f_exp, f_val, rel_tol=1e-5):
                    return True, "Scalar vs. Row match"
            else:
                if str(expected_scalar) == str(val):
                    return True, "Scalar vs. Row match"

    # Rule 2: Column-Name Agnostic Superset Matching
    if len(df_expected) == len(df_generated):
        all_expected_found = True
        matched_gen_cols = set()
        for exp_col_name in df_expected.columns:
            exp_arr = df_expected[exp_col_name].values
            col_found = False
            for i, gen_col_name in enumerate(df_generated.columns):
                if i in matched_gen_cols:
                    continue
                gen_arr = df_generated[gen_col_name].values
                if _arrays_match(exp_arr, gen_arr):
                    col_found = True
                    matched_gen_cols.add(i)
                    break
            if not col_found:
                all_expected_found = False
                break
        if all_expected_found:
            return True, "Column-Name Agnostic Superset Match"

    # Fallback: Exact pandas comparison
    try:
        pd.testing.assert_frame_equal(
            df_expected, df_generated,
            check_dtype=False, check_index_type=False,
        )
        return True, "Exact match"
    except AssertionError:
        pass

    return False, "Mismatch in values or shape"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: AST DIAGNOSTICS (deterministic sqlglot analysis)
# ═══════════════════════════════════════════════════════════════════════════════
# For each query, we parse both expected and generated SQL into ASTs and check
# whether the structural clauses present in the expected SQL are also present
# in the generated SQL.
#
# Return values per clause:
#   True  — expected has the clause AND generated has it too
#   False — expected has the clause BUT generated is missing it
#   None  — expected does NOT use this clause (N/A for this query)

def _get_select_columns(ast) -> set:
    """Extract column names referenced in SELECT expressions."""
    cols = set()
    select = ast.find(exp.Select)
    if not select:
        return cols
    for expr in select.expressions:
        for col in expr.find_all(exp.Column):
            cols.add(col.name.lower())
        if isinstance(expr, exp.Star):
            cols.add("*")
    return cols


def ast_diagnostics(expected_sql: str, generated_sql: str) -> dict:
    """Compare structural elements of expected vs generated SQL using sqlglot.

    Returns a dict of 8 AST match flags (True / False / None).
    """
    try:
        exp_parsed = sqlglot.parse(expected_sql, read="postgres")
        gen_parsed = sqlglot.parse(generated_sql, read="postgres")
        if not exp_parsed or not gen_parsed or not exp_parsed[0] or not gen_parsed[0]:
            return _empty_diagnostics()
        exp_ast = exp_parsed[0]
        gen_ast = gen_parsed[0]
    except Exception:
        return _empty_diagnostics()

    def has_node(ast, node_type):
        return ast.find(node_type) is not None

    def check_clause(node_type):
        """Check if a clause present in expected is also present in generated."""
        if not has_node(exp_ast, node_type):
            return None  # Expected doesn't use this clause → N/A
        return has_node(gen_ast, node_type)

    # SELECT: check column overlap between expected and generated
    def check_select():
        exp_cols = _get_select_columns(exp_ast)
        gen_cols = _get_select_columns(gen_ast)
        if not exp_cols or "*" in exp_cols:
            return None  # Can't meaningfully compare SELECT *
        if not gen_cols:
            return False
        # Expected columns should be a subset of generated columns
        return exp_cols.issubset(gen_cols)

    # SUBQUERY: check for exp.Subquery nodes (parenthesized nested SELECTs)
    def check_subquery():
        if not has_node(exp_ast, exp.Subquery):
            return None
        return has_node(gen_ast, exp.Subquery)

    return {
        "ast_select_match": check_select(),
        "ast_filter_match": check_clause(exp.Where),
        "ast_join_match": check_clause(exp.Join),
        "ast_groupby_match": check_clause(exp.Group),
        "ast_having_match": check_clause(exp.Having),
        "ast_orderby_match": check_clause(exp.Order),
        "ast_subquery_match": check_subquery(),
        "ast_union_match": check_clause(exp.Union),
    }


def _empty_diagnostics() -> dict:
    """Return an all-None diagnostics dict (used when SQL can't be parsed)."""
    return {
        "ast_select_match": None,
        "ast_filter_match": None,
        "ast_join_match": None,
        "ast_groupby_match": None,
        "ast_having_match": None,
        "ast_orderby_match": None,
        "ast_subquery_match": None,
        "ast_union_match": None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: TERMINAL DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

AST_LABELS = {
    "ast_select_match": "SELECT",
    "ast_filter_match": "FILTER",
    "ast_join_match": "JOIN",
    "ast_groupby_match": "GROUP BY",
    "ast_having_match": "HAVING",
    "ast_orderby_match": "ORDER BY",
    "ast_subquery_match": "SUBQUERY",
    "ast_union_match": "UNION",
}


def print_dashboard(results: list, pattern_stats: dict, safety_stats: dict):
    """Print the final evaluation dashboard to the terminal."""
    total = len(results)
    passed = sum(1 for r in results if r["execution_pass"])
    pct = (passed / total * 100) if total else 0

    print(f"\n{'═' * W}")
    print(f"  📊  EVALUATION SUMMARY")
    print(f"{'═' * W}")

    # ── Execution Accuracy ────────────────────────────────────────────────
    print(f"\n  Execution Accuracy")
    print(f"  {'─' * (W - 4)}")
    bar_len = 40
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"  [{bar}] {passed}/{total} ({pct:.1f}%)")

    # ── Pattern Accuracy ──────────────────────────────────────────────────
    print(f"\n  Pattern Accuracy")
    print(f"  {'─' * (W - 4)}")
    for pat in sorted(pattern_stats.keys()):
        stats = pattern_stats[pat]
        total_p = stats["pass"] + stats["fail"]
        pct_p = (stats["pass"] / total_p * 100) if total_p else 0
        print(f"  {pat:<30} {stats['pass']:>2}/{total_p:<2} ({pct_p:.1f}%)")

    # ── AST Diagnostics ───────────────────────────────────────────────────
    print(f"\n  AST Diagnostics")
    print(f"  {'─' * (W - 4)}")
    for key in AST_LABELS:
        label = AST_LABELS[key]
        applicable = [r[key] for r in results if r[key] is not None]
        if not applicable:
            print(f"  {label:<15} N/A")
        else:
            correct = sum(1 for v in applicable if v)
            pct_a = (correct / len(applicable) * 100)
            print(f"  {label:<15} {correct:>2}/{len(applicable):<2} ({pct_a:.1f}%)")

    # ── Safety Layer ──────────────────────────────────────────────────────
    print(f"\n  Safety Layer")
    print(f"  {'─' * (W - 4)}")
    print(f"  Triggered:        {safety_stats['triggered']}")
    print(f"  Recovered:        {safety_stats['recovered']}")
    print(f"  Failed:           {safety_stats['failed']}")
    if safety_stats["triggered"] > 0:
        print(f"  Avg Attempts:     {safety_stats['avg_attempts']:.1f}")

    # ── Dataset Breakdown ─────────────────────────────────────────────────
    print(f"\n  Dataset Breakdown")
    print(f"  {'─' * (W - 4)}")
    for source in ["golden", "advanced"]:
        src_results = [r for r in results if r["dataset_source"] == source]
        if src_results:
            src_pass = sum(1 for r in src_results if r["execution_pass"])
            src_pct = (src_pass / len(src_results) * 100)
            print(f"  {source.capitalize():<15} {src_pass}/{len(src_results)} ({src_pct:.1f}%)")

    print(f"\n{'═' * W}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EVALUATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_evaluation():
    """Main entry point: run the full unified evaluation."""

    # ── Load dataset ──────────────────────────────────────────────────────
    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    total = len(dataset)
    print(f"\n{'═' * W}")
    print(f"  🚀  UNIFIED TEXT-TO-SQL EVALUATION")
    print(f"  📦 Loaded {total} queries from evaluation_dataset.json")
    print(f"{'═' * W}")

    results = []
    pattern_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
    safety_stats = {
        "triggered": 0,
        "recovered": 0,
        "failed": 0,
        "total_attempts": 0,
    }

    for idx, item in enumerate(dataset, 1):
        question = item["question"]
        expected_sql = item["expected_sql"]
        patterns = item.get("patterns", [])
        dataset_source = item.get("dataset_source", "unknown")

        t_start = time.time()
        print(f"\n  [{idx}/{total}] {item['id']}")
        print(f"  ❓ {question}")

        # ── Phase 1: Generation + Safety Layer Metrics ────────────────────
        try:
            gen_sql, contexts, filters, safety = run_pipeline_with_safety_metrics(question)
        except Exception as e:
            gen_sql = f"PIPELINE_ERROR: {e}"
            contexts, filters = [], {}
            safety = {
                "safety_triggered": False,
                "self_heal_attempts": 0,
                "validation_status": f"Pipeline Error: {e}",
            }

        # Record safety stats
        if safety["safety_triggered"]:
            safety_stats["triggered"] += 1
            safety_stats["total_attempts"] += safety["self_heal_attempts"]
            if "Passed" in safety["validation_status"]:
                safety_stats["recovered"] += 1
            else:
                safety_stats["failed"] += 1

        # ── Phase 2: Execution Accuracy ───────────────────────────────────
        df_expected, err_exp = execute_sql_safely(expected_sql)
        df_generated, err_gen = execute_sql_safely(gen_sql)

        execution_pass = False
        failure_reason = ""

        if err_exp or err_gen:
            failure_reason = f"DB Error. Expected: {err_exp} | Generated: {err_gen}"
        elif df_expected is None:
            failure_reason = "Expected SQL returned None"
        elif df_generated is None:
            failure_reason = "Generated SQL returned None"
        else:
            execution_pass, failure_reason = compare_result_sets(df_expected, df_generated)

        # ── Phase 3: AST Diagnostics ──────────────────────────────────────
        diag = ast_diagnostics(expected_sql, gen_sql)

        # ── Phase 4: Pattern Accuracy ─────────────────────────────────────
        for p in patterns:
            if execution_pass:
                pattern_stats[p]["pass"] += 1
            else:
                pattern_stats[p]["fail"] += 1

        elapsed = time.time() - t_start
        status = "✅ PASS" if execution_pass else "❌ FAIL"
        print(f"  🤖 SQL: {gen_sql[:100]}{'...' if len(gen_sql) > 100 else ''}")
        print(f"  {status} ({failure_reason}) [{elapsed:.1f}s]")
        if safety["safety_triggered"]:
            healed = "Recovered" if "Passed" in safety["validation_status"] else "Blocked"
            print(f"  🛡️  Safety: {healed} after {safety['self_heal_attempts']} retries")

        # ── Collect full result row ───────────────────────────────────────
        result = {
            "query_id": item["id"],
            "dataset_source": dataset_source,
            "question": question,
            "generated_sql": gen_sql,
            "expected_sql": expected_sql,
            "execution_pass": execution_pass,
            "failure_reason": failure_reason,
            "patterns": ", ".join(patterns),
            "safety_triggered": safety["safety_triggered"],
            "self_heal_attempts": safety["self_heal_attempts"],
            "validation_status": safety["validation_status"],
        }
        # Merge AST diagnostics into the result row
        result.update(diag)
        results.append(result)

    # ── Phase 5: Safety Layer Analytics ───────────────────────────────────
    if safety_stats["triggered"] > 0:
        safety_stats["avg_attempts"] = (
            safety_stats["total_attempts"] / safety_stats["triggered"]
        )
    else:
        safety_stats["avg_attempts"] = 0.0

    # ── Phase 6: Report Generation ────────────────────────────────────────
    df = pd.DataFrame(results)
    df.to_csv(REPORT_CSV_PATH, index=False)
    print(f"\n  📁 Report saved to: {REPORT_CSV_PATH}")

    print_dashboard(results, pattern_stats, safety_stats)


if __name__ == "__main__":
    run_evaluation()
