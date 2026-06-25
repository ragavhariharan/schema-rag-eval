"""
scope.py
═════════════════════════════════════════════════════════════════════════════════
Scope labels + agent routing for the SQL Agent.

Scope classification is now part of the single combined understanding call in
`conversation.understand()` (merged for latency). This module keeps:
  • ROUTE_TO        — scope → which agent should handle it
  • classify_scope  — a thin wrapper returning just the scope, used by the scope
                      eval (run_scope_eval.py) and the debug tool.
═════════════════════════════════════════════════════════════════════════════════
"""
from conversation import understand, SCOPE_LABELS  # noqa: F401  (re-exported)

# scope → which agent should handle it (None = handle conversationally here)
ROUTE_TO = {
    "calculation": "calculation_agent",
    "domain": "domain_agent",
    "chitchat": None,
    "sql": None,
}


def classify_scope(query: str) -> dict:
    """Return just the scope label for a query (no history). Thin wrapper over the
    combined understanding call."""
    return {"scope": understand(query)["scope"], "reason": ""}
