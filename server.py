"""
server.py
═════════════════════════════════════════════════════════════════════════════════
EarthTekniks Lens Catalog — MCP server (FastMCP).

A decoupled, use-case-agnostic tool layer over the Supabase lens catalog, for any
LLM client (Claude Agent SDK, an ADK, the multi-agent orchestrator). The client
supplies the reasoning; this server supplies indexed, safe, schema-aware tools.

Deterministic core (always on, no LLM): schema discovery, model lookup, structured
search, cross-table superlatives, and a validated read-only SQL escape hatch.

Optional (ETK_ENABLE_PIPELINE_TOOL=1, needs Ollama): query_catalog — delegate a
whole natural-language request to the local pipeline.

Run:
    python server.py                 # stdio (Claude Desktop, MCP Inspector)
    python server.py --http          # streamable HTTP (orchestrator / remote)
═════════════════════════════════════════════════════════════════════════════════
"""
import argparse
import os
from typing import Optional

from fastmcp import FastMCP

from etk_mcp import indexes, query

mcp = FastMCP("EarthTekniks Lens Catalog")


# ── Schema discovery (served from in-memory indexes; no DB hit) ──────────────────

@mcp.tool
def list_families() -> list:
    """List the lens families (e.g. fa_lens, telecentric, line_scan, macro, zoom,
    microscope, spectral, m12_mount, autofocus, accessory) and the database tables
    in each. Start here to understand what the catalog contains."""
    return indexes.list_families()


@mcp.tool
def list_tables(family: Optional[str] = None) -> list:
    """List catalog tables with a one-line purpose each. Pass `family` to filter to
    one family (see list_families). Use this to pick the right table before
    describe_table / search_products."""
    return indexes.list_tables(family)


@mcp.tool
def describe_table(table: str) -> dict:
    """Describe a table: its columns, purpose, signature columns, and IMPORTANT
    unit/synonym caveats (e.g. three_cmos working distance is in METRES not mm;
    sensor_raw vs sensor_size_raw mean the same thing). ALWAYS describe_table before
    writing SQL against it with run_select."""
    return indexes.describe_table(table)


@mcp.tool
def lookup_model(name: str) -> dict:
    """Find which table/family a lens MODEL NAME belongs to (e.g. 'FA0401C').
    Handles exact, case/space-insensitive, and partial matches; returns suggestions
    when there's no exact hit. Served from the model index — no DB hit."""
    return indexes.find_model(name)


# ── Data access (read-only, validated, cached) ──────────────────────────────────

@mcp.tool
def get_product(model_name: str) -> dict:
    """Get the full specification row(s) for a specific lens model name. Resolves
    the model to its table automatically (a few model names appear in two tables —
    both rows are returned)."""
    return query.get_product(model_name)


@mcp.tool
def search_products(
    table: Optional[str] = None,
    family: Optional[str] = None,
    filters: Optional[list] = None,
    columns: Optional[list] = None,
    sort: Optional[dict] = None,
    limit: int = 50,
) -> dict:
    """Filtered search over one `table` or a whole `family` (one of them is required).

    filters: list of {"column": str, "op": str, "value": any} — op is one of
             =, !=, <, <=, >, >=, ILIKE, LIKE, IS NULL, IS NOT NULL.
    columns: spec columns to return (model_name is always included).
    sort:    {"column": str, "direction": "asc"|"desc"}.
    When `family` spans several tables, results are combined with UNION ALL across
    every table that has the requested columns. Only whitelisted columns are allowed."""
    return query.search_products(table, family, filters, columns, sort, limit)


@mcp.tool
def find_extreme(metric: str, scope: str = "all", direction: str = "min", limit: int = 1) -> dict:
    """Superlative lookup across many tables — e.g. cheapest/most-expensive,
    lightest/heaviest, widest aperture.

    metric: the spec column to rank by (e.g. list_price, weight_g, f_no_min).
    scope:  "all" (whole catalog), a family name, or a single table name.
    direction: "min" (smallest/cheapest) or "max" (largest/most expensive).
    Combines all tables that have `metric` with UNION ALL, then ranks — so
    'cheapest lens overall' = find_extreme("list_price", "all", "min")."""
    return query.find_extreme(metric, scope, direction, limit)


@mcp.tool
def run_select(sql: str) -> dict:
    """Run a custom read-only PostgreSQL SELECT against the catalog. The query is
    validated first: read-only is enforced and every table/column must exist
    (no writes, no DDL, no hallucinated columns). Results are row-capped. Prefer the
    structured tools above; use this for joins/aggregates/complex filters they can't
    express. Call describe_table first so you use real column names."""
    return query.run_select(sql)


def _register_optional_tools():
    """Register the Ollama-backed pipeline tool only when explicitly enabled."""
    if os.getenv("ETK_ENABLE_PIPELINE_TOOL", "").strip() in ("1", "true", "True"):
        from etk_mcp.pipeline_tool import query_catalog

        @mcp.tool
        def query_catalog_tool(request: str, history: Optional[list] = None) -> dict:
            """Delegate a whole natural-language lens-catalog request to the LOCAL
            pipeline (it understands, routes, writes SQL, and runs it). Use when you
            want the local models to handle the catalog query end-to-end instead of
            composing the deterministic tools yourself. Returns {sql, rows, assumption}
            or {clarification} if the request is too vague."""
            return query_catalog(request, history)


_register_optional_tools()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="EarthTekniks Lens Catalog MCP server")
    ap.add_argument("--http", action="store_true", help="serve over streamable HTTP")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()
