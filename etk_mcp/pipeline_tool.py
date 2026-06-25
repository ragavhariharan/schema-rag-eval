"""
etk_mcp/pipeline_tool.py
═════════════════════════════════════════════════════════════════════════════════
OPTIONAL pipeline-as-a-tool.

Wraps the agent's local-LLM pipeline (understanding + routing + SQL generation +
UNION-expander) so an orchestrator can DELEGATE a whole natural-language catalog
request to the local models instead of writing SQL itself.

This module lazily imports `pipeline` / `conversation` (which pull in Ollama and
ChromaDB) INSIDE the function — so importing it is cheap, and the deterministic
core never depends on it. The server only registers this tool when
ETK_ENABLE_PIPELINE_TOOL=1.

Note: deliberately NO scope gate / handoff — routing is the orchestrator's job.
═════════════════════════════════════════════════════════════════════════════════
"""


def query_catalog(request: str, history: list = None) -> dict:
    """Answer a natural-language lens-catalog request using the local pipeline.

    Returns {sql, rows, row_count, assumption} — or {clarification} if the request
    is too vague, or {error} on failure.
    """
    try:
        from conversation import understand
        from pipeline import run_pipeline, execute_sql_safely
    except Exception as e:  # pragma: no cover - import/env issues
        return {"error": f"Pipeline tool unavailable: {e}"}

    # Resolve follow-ups / capture assumptions (ignore scope — orchestrator routes).
    u = understand(request, history)
    if not u["answerable"]:
        return {"clarification": u["clarifying_question"]}

    standalone = u["standalone_query"]
    try:
        sql, _contexts, _filters = run_pipeline(standalone)
    except Exception as e:
        return {"error": f"SQL generation failed: {e}", "request": standalone}

    df, err = execute_sql_safely(sql)
    if err:
        return {"error": err, "sql": sql}

    rows = df.to_dict("records") if df is not None else []
    return {
        "sql": sql,
        "rows": rows,
        "row_count": len(rows),
        "assumption": u.get("assumption"),
    }
