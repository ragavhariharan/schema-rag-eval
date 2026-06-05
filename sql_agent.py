"""
sql_agent.py
═══════════════════════════════════════════════════════════════════════════════════
SQL Agent (SQA) — Data Retrieval Layer for the EarthTekniks AI System.

The SQL Agent is the sole owner of database access and product retrieval.
It provides a controlled, read-only interface between the engineering system
and external product databases.

Responsibilities (per architecture doc Section 9):
  9.1  Database Schema Understanding     → schema_registry.json
  9.2  Query Generation                  → Structured filters OR NL via RAG pipeline
  9.3  Query Validation                  → SQLValidator (sqlglot)
  9.4  Query Execution                   → psycopg2 against Supabase PostgreSQL
  9.5  Result Normalization              → DataFrame → {"products": [...]}
  9.6  Empty Result Detection            → {"status": "no_results"}
  9.7  Database Error Handling           → {"status": "error", "error_type": "..."}
  9.8  Read-Only Enforcement             → Validator + readonly psycopg2 connection
  9.9  State Updates                     → Reads state["filters"], writes state["products"]

Execution Flow:
  Receive Search Filters → Validate Filters → Generate SQL Query →
  Validate Query → Execute Against External Database → Normalize Results →
  Write Products To State → Return Control To Router
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os

import pandas as pd

from sql_validator import SQLValidator
from run_execution_accuracy import run_pipeline, execute_sql_safely

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════════
# FILTER-TO-SQL OPERATOR MAPPING
# ═══════════════════════════════════════════════════════════════════════════════
# The Domain Agent passes structured filters using MongoDB-style operators.
# This map translates them to their PostgreSQL equivalents for query building.

OPERATOR_MAP = {
    "$gte": ">=",
    "$lte": "<=",
    "$gt": ">",
    "$lt": "<",
    "$eq": "=",
    "$ne": "!=",
    "$in": "IN",
}


class SQLAgent:
    """SQL Agent — the data retrieval layer of the EarthTekniks AI system.

    The SQL Agent does NOT perform engineering reasoning, formula execution,
    product ranking, or recommendation logic. It only retrieves data from
    external databases.

    Usage:
        agent = SQLAgent()
        state = agent.execute(state)  # state["products"] is now populated
    """

    def __init__(self):
        # ── 9.1: Database Schema Understanding ────────────────────────────
        # Load the schema registry — our ground truth for table/column names.
        # This lets us validate filters and SQL before touching the database.
        registry_path = os.path.join(SCRIPT_DIR, "schema_registry.json")
        with open(registry_path, "r") as f:
            self.schema = json.load(f)
        self.valid_tables = set(self.schema.keys())

        # ── 9.3 + 9.8: Query Validation + Read-Only Enforcement ──────────
        # SQLValidator uses sqlglot AST analysis to enforce syntax, table/column
        # grounding, and read-only constraints before any SQL reaches the DB.
        self.validator = SQLValidator(registry_path)

    # ═══════════════════════════════════════════════════════════════════════
    # 9.9: MAIN ENTRY POINT — STATE IN, STATE OUT
    # ═══════════════════════════════════════════════════════════════════════

    def execute(self, state: dict) -> dict:
        """Full SQL Agent execution flow.

        Routing logic:
          - If state["filters"] is populated → Structured filter path
            (deterministic filter-to-SQL translation, no LLM involved)
          - If state["user_input"] is populated → Natural language path
            (uses existing RAG pipeline with LLM generation + self-healing)
          - If neither → Error response

        Reads:  state["filters"] OR state["user_input"]
        Writes: state["products"], state["sql_agent_result"]
        May append to: state["errors"]

        Returns the updated state dict.
        """
        filters = state.get("filters", {})
        user_input = state.get("user_input", "")

        # Route to the appropriate execution path
        if filters:
            result = self._execute_from_filters(filters)
        elif user_input:
            result = self._execute_from_natural_language(user_input)
        else:
            result = self._error_response(
                "no_input", "No filters or user input provided to SQL Agent"
            )

        # ── 9.9: Write products to state ──────────────────────────────────
        state["products"] = result.get("products", [])

        # Append error to state's error log if the execution failed
        if result.get("status") == "error":
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "source": "SQA",
                "error_type": result.get("error_type", "unknown"),
                "message": result.get("message", ""),
            })

        # Attach the full result dict for the Router to inspect
        state["sql_agent_result"] = result

        return state

    # ═══════════════════════════════════════════════════════════════════════
    # STRUCTURED FILTER PATH (Domain Agent → SQL Agent)
    # ═══════════════════════════════════════════════════════════════════════
    # This path is used when the Domain Agent has already performed
    # engineering reasoning and produced structured database filters.
    # No LLM is involved — the translation is purely deterministic.

    def _execute_from_filters(self, filters: dict) -> dict:
        """Translate structured filters into SQL, validate, execute, normalize.

        Expected filter format (MongoDB-style operators):
            {
                "table": "line_scan_lens_8k5u",
                "list_price": {"$lt": 1000},
                "weight_g": {"$lt": 200}
            }

        The "table" key is required and specifies the target table.
        All other keys are filter conditions.
        """
        # Work on a copy to avoid mutating the caller's dict
        filters = filters.copy()

        # ── Step 1: Extract and validate table ────────────────────────────
        table = filters.pop("table", None)
        if not table:
            return self._error_response(
                "missing_table",
                "No 'table' key specified in filters. "
                "The Domain Agent must specify which table to query.",
            )

        if table not in self.valid_tables:
            return self._error_response(
                "invalid_table",
                f"Table '{table}' does not exist in the schema registry.",
                table=table,
            )

        # ── Step 2: Validate filter columns exist in the target table ─────
        valid_columns = set(self.schema[table])
        for col in filters:
            if col not in valid_columns:
                return self._error_response(
                    "invalid_column",
                    f"Column '{col}' does not exist in table '{table}'.",
                    column=col,
                    table=table,
                )

        # ── Step 3: Translate filters to SQL (9.2) ────────────────────────
        sql = self._translate_filters_to_sql(table, filters)

        # ── Step 4: Validate the generated SQL (9.3 + 9.8) ───────────────
        val_result = self.validator.validate(sql)
        if not val_result.is_valid:
            return self._error_response("validation_failure", val_result.reason)

        # ── Step 5: Execute against the database (9.4) ────────────────────
        df, error = execute_sql_safely(sql)

        # ── Step 6: Handle database errors (9.7) ─────────────────────────
        if error:
            return self._error_response(
                "query_execution_error", error, sql=sql
            )

        # ── Step 7: Normalize and detect empty results (9.5 + 9.6) ───────
        return self._normalize_results(df, sql=sql)

    # ═══════════════════════════════════════════════════════════════════════
    # NATURAL LANGUAGE PATH (User → RAG Pipeline → SQL Agent)
    # ═══════════════════════════════════════════════════════════════════════
    # This path is the fallback for interactive testing or when the Domain
    # Agent hasn't processed the query yet. It uses the existing proven
    # RAG pipeline: filter extraction → ChromaDB retrieval → LLM SQL
    # generation → self-healing validation loop.

    def _execute_from_natural_language(self, question: str) -> dict:
        """Generate SQL from a natural language question using the RAG pipeline.

        Uses run_pipeline() which internally handles:
          - Metadata filter extraction via LLM
          - ChromaDB schema context retrieval
          - SQL generation via LLM
          - Self-healing validation loop (up to 2 retries)
        """
        # ── Step 1: Generate SQL via the RAG pipeline ─────────────────────
        try:
            gen_sql, contexts, extracted_filters = run_pipeline(question)
        except Exception as e:
            return self._error_response(
                "query_generation_error",
                f"RAG pipeline failed: {str(e)}",
            )

        # ── Step 2: Execute against the database (9.4) ────────────────────
        df, error = execute_sql_safely(gen_sql)

        # ── Step 3: Handle database errors (9.7) ─────────────────────────
        if error:
            return self._error_response(
                "query_execution_error", error, sql=gen_sql
            )

        # ── Step 4: Normalize and detect empty results (9.5 + 9.6) ───────
        return self._normalize_results(df, sql=gen_sql)

    # ═══════════════════════════════════════════════════════════════════════
    # 9.2: FILTER-TO-SQL TRANSLATION ENGINE
    # ═══════════════════════════════════════════════════════════════════════

    def _translate_filters_to_sql(self, table: str, filters: dict) -> str:
        """Translate a MongoDB-style filter dict into an executable SQL query.

        Supports operators: $gte, $lte, $gt, $lt, $eq, $ne, $in

        Examples:
            {"list_price": {"$lt": 1000}}
              → SELECT * FROM table WHERE list_price < 1000

            {"mount_raw": {"$eq": "C-mount"}, "weight_g": {"$lt": 200}}
              → SELECT * FROM table WHERE mount_raw = 'C-mount' AND weight_g < 200

            {"mount_raw": {"$in": ["C-mount", "F-mount"]}}
              → SELECT * FROM table WHERE mount_raw IN ('C-mount', 'F-mount')
        """
        conditions = []

        for column, constraint in filters.items():
            if isinstance(constraint, dict):
                # Operator-based constraint: {"$gte": 5}
                for op, value in constraint.items():
                    if op not in OPERATOR_MAP:
                        continue  # Skip unknown operators gracefully
                    if op == "$in":
                        # IN clause: list of values
                        formatted_values = ", ".join(
                            self._quote_value(v) for v in value
                        )
                        conditions.append(f"{column} IN ({formatted_values})")
                    else:
                        sql_op = OPERATOR_MAP[op]
                        conditions.append(
                            f"{column} {sql_op} {self._quote_value(value)}"
                        )
            else:
                # Direct equality shorthand: {"column": value}
                conditions.append(
                    f"{column} = {self._quote_value(constraint)}"
                )

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"SELECT * FROM {table} WHERE {where_clause};"
        else:
            return f"SELECT * FROM {table};"

    def _quote_value(self, value) -> str:
        """Safely quote a filter value for SQL interpolation.

        Numbers are left unquoted. Booleans become TRUE/FALSE.
        Strings are single-quoted with internal quotes escaped.
        """
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(value)
        # String: escape single quotes to prevent injection
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

    # ═══════════════════════════════════════════════════════════════════════
    # 9.5 + 9.6: RESULT NORMALIZATION + EMPTY RESULT DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _normalize_results(self, df: pd.DataFrame, sql: str = "") -> dict:
        """Convert a pandas DataFrame into the normalized product response format.

        If the DataFrame is empty, returns a "no_results" status so the Router
        can trigger recovery (Router → DA → Identify Limiting Constraint).
        """
        if df is None or df.empty:
            return {
                "products": [],
                "count": 0,
                "status": "no_results",
                "sql": sql,
            }

        # Convert DataFrame rows to a list of dicts for JSON serialization
        products = df.to_dict(orient="records")

        return {
            "products": products,
            "count": len(products),
            "status": "success",
            "sql": sql,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 9.7: DATABASE ERROR HANDLING
    # ═══════════════════════════════════════════════════════════════════════

    def _error_response(self, error_type: str, message: str, **kwargs) -> dict:
        """Build a structured error response.

        The Router inspects this to decide: Retry, Escalate, or Notify user.

        Error types:
          - no_input              : No filters or user_input in state
          - missing_table         : Filters missing the required "table" key
          - invalid_table         : Table doesn't exist in schema registry
          - invalid_column        : Column doesn't exist in the target table
          - validation_failure    : SQL failed sqlglot validation
          - query_generation_error: RAG pipeline crashed
          - query_execution_error : Database execution failed
        """
        response = {
            "products": [],
            "count": 0,
            "status": "error",
            "error_type": error_type,
            "message": message,
        }
        response.update(kwargs)
        return response
