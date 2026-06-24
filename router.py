"""
router.py
═════════════════════════════════════════════════════════════════════════════════
Phase 2 — Deterministic-first TABLE ROUTER.

Given a natural-language query that does NOT name a specific model (Phase 1
handles those), decide which database table(s) can answer it. This replaces the
old single-dimension `product_type` filter, which only worked when the lens
family was stated explicitly and could only see 3 of 32 tables.

Strategy:
  1. Present a compact catalog of all tables (purpose + distinctive columns) to
     the local LLM and ask it to select the minimal relevant table set, flagging
     cross-table ("compare across all lenses") queries.
  2. Validate the returned names against the real table list (drop hallucinations).
  3. Fall back to "no decision" (empty) if the model returns nothing usable, so
     the pipeline can degrade to broad semantic retrieval.

Backed by table_catalog.json (built by build_table_catalog.py).
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os

import ollama

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TABLE_CATALOG_PATH = os.path.join(SCRIPT_DIR, "table_catalog.json")

_catalog = None


def _load_catalog() -> dict:
    global _catalog
    if _catalog is None:
        try:
            with open(TABLE_CATALOG_PATH, "r", encoding="utf-8") as f:
                _catalog = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _catalog = {}
    return _catalog


def get_all_tables() -> list:
    """All known table names (used to expand cross-table queries)."""
    return list(_load_catalog().keys())


def _catalog_prompt_block(catalog: dict) -> str:
    """Render the catalog as one compact line per table for the router prompt."""
    lines = []
    for table, e in catalog.items():
        purpose = (e.get("purpose") or "")[:160]
        sig = ", ".join(e.get("signature_columns", [])[:8])
        lines.append(f"- {table} [{e.get('family','?')}]: {purpose} | key cols: {sig}")
    return "\n".join(lines)


def route_tables(user_query: str) -> dict:
    """Select the table(s) relevant to a query.

    Returns:
        {"tables": [validated table names], "cross_table": bool}
        — tables is [] when the router can't decide (caller falls back).
    """
    catalog = _load_catalog()
    if not catalog:
        return {"tables": [], "cross_table": False}

    valid_tables = set(catalog.keys())

    # Single source of truth for the model name (lazy import avoids a cycle).
    from pipeline import OLLAMA_MODEL

    system_prompt = f"""You are a table router for an industrial machine-vision lens catalog.
Given the user's question, choose the database table(s) that can answer it.

TABLES (name [family]: purpose | distinctive columns):
{_catalog_prompt_block(catalog)}

Return ONLY a JSON object:
{{"tables": ["<table_name>", ...], "cross_table": true/false}}

RULES:
- Use ONLY exact table names from the list above. Never invent names.
- Pick the MINIMAL set of tables that can answer the question.
- If the query targets one lens family that spans several tables (e.g. "telecentric"),
  include all tables of that family.
- If the query compares across many lens types or says "any/all/overall lenses"
  without naming a family, set "cross_table" to true and include every table that
  has the requested attribute.
- If you cannot tell, return an empty "tables" list."""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            format="json",
            options={"temperature": 0, "num_ctx": 8192},
        )
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError, Exception):
        return {"tables": [], "cross_table": False}

    raw_tables = parsed.get("tables") or []
    if not isinstance(raw_tables, list):
        return {"tables": [], "cross_table": False}

    # Validate against the real table list, preserve order, dedupe.
    tables = []
    for t in raw_tables:
        if isinstance(t, str) and t in valid_tables and t not in tables:
            tables.append(t)

    return {"tables": tables, "cross_table": bool(parsed.get("cross_table"))}
