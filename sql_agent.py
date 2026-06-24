"""
sql_agent.py
═══════════════════════════════════════════════════════════════════════════════════
SQL Agent (SQA) — Data Retrieval Layer for the EarthTekniks AI System.

Sole owner of database access and product retrieval: provides a controlled,
read-only interface between natural-language queries and the product database.

Responsibilities:
  9.1  Database Schema Understanding     → schema_registry.json
  9.2  Query Generation                  → NL via RAG pipeline
  9.3  Query Validation                  → SQLValidator (sqlglot)
  9.4  Query Execution                   → psycopg2 against Supabase PostgreSQL
  9.5  Result Normalization              → DataFrame → {"products": [...]}
  9.6  Empty Result Detection            → {"status": "no_results"}
  9.7  Database Error Handling           → {"status": "error", "error_type": "..."}
  9.8  Read-Only Enforcement             → Validator + readonly psycopg2 connection
  9.9  State Updates                     → Reads state["user_input"], writes state["products"]

Execution Flow:
  Natural Language Query → Scope Gate → Conversational Rewrite →
  Schema-RAG Retrieval → SQL Generation → Validation → Execution → Normalize Results
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os

import pandas as pd

from sql_validator import SQLValidator
from pipeline import run_pipeline, execute_sql_safely, resolve_models
from scope import classify_scope
from conversation import assess_query

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
        registry_path = os.path.join(SCRIPT_DIR, "schema_registry.json")
        # ── 9.3 + 9.8: Query Validation + Read-Only Enforcement ──────────
        # SQLValidator uses sqlglot AST analysis to enforce syntax, table/column
        # grounding, and read-only constraints before any SQL reaches the DB.
        self.validator = SQLValidator(registry_path)

    # ═══════════════════════════════════════════════════════════════════════
    # 9.9: MAIN ENTRY POINT — STATE IN, STATE OUT
    # ═══════════════════════════════════════════════════════════════════════

    def execute(self, state: dict) -> dict:
        """Full SQL Agent execution flow.

        The SQL workflow has a single execution path:
          Natural Language Query
              ↓
          Schema-RAG Retrieval
              ↓
          SQL Generation
              ↓
          Validation
              ↓
          Execution

        Reads:  state["user_input"]
        Writes: state["products"], state["sql_agent_result"]
        May append to: state["errors"]

        Returns the updated state dict.
        """
        user_input = state.get("user_input", "").strip()
        history = state.get("history", []) or []

        # Route to the appropriate execution path
        if not user_input:
            result = self._error_response(
                "no_input", "No user input provided to SQL Agent"
            )
        elif resolve_models(user_input):
            # Fast path: a catalog model name is named → definitely in scope and
            # self-contained; skip the scope/understanding steps.
            result = self._execute_from_natural_language(user_input)
        else:
            # ── Phase 3: scope gate ───────────────────────────────────────
            # Decline cleanly if the query isn't a catalog lookup.
            scope = classify_scope(user_input)
            if scope["scope"] != "sql":
                result = self._out_of_scope_response(scope)
            else:
                # ── Phase 5: conversational understanding ─────────────────
                # Resolve follow-ups against history; ask one question if the
                # request is too vague; capture any interpretation as an
                # assumption to surface in the answer.
                assessment = assess_query(user_input, history)
                if not assessment["answerable"]:
                    result = self._clarification_response(
                        assessment["clarifying_question"]
                    )
                else:
                    result = self._execute_from_natural_language(
                        assessment["standalone_query"]
                    )
                    if assessment.get("assumption"):
                        result["assumption"] = assessment["assumption"]

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

        # Attach the full result dict for downstream inspection
        state["sql_agent_result"] = result

        return state

    # ═══════════════════════════════════════════════════════════════════════
    # NATURAL LANGUAGE PATH (User → RAG Pipeline → SQL Agent)
    # ═══════════════════════════════════════════════════════════════════════
    # Uses the RAG pipeline: filter extraction → ChromaDB retrieval → LLM SQL
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
    # 9.5 + 9.6: RESULT NORMALIZATION + EMPTY RESULT DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _normalize_results(self, df: pd.DataFrame, sql: str = "") -> dict:
        """Convert a pandas DataFrame into the normalized product response format.

        If the DataFrame is empty, returns a "no_results" status.
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

        Error types:
          - no_input              : No user_input in state
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

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3: OUT-OF-SCOPE GATE
    # ═══════════════════════════════════════════════════════════════════════

    def _out_of_scope_response(self, scope: dict) -> dict:
        """Build a response for a query that isn't a catalog lookup."""
        return {
            "products": [],
            "count": 0,
            "status": "out_of_scope",
            "message": scope.get("reason", ""),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 5: CLARIFICATION
    # ═══════════════════════════════════════════════════════════════════════

    def _clarification_response(self, question: str) -> dict:
        """Build a response that asks the user one clarifying question instead
        of guessing at an under-specified query."""
        return {
            "products": [],
            "count": 0,
            "status": "needs_clarification",
            "message": question or "Could you give a bit more detail about what you're looking for?",
        }
