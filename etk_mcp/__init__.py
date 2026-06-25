"""
etk_mcp — decoupled data-access package for the EarthTekniks Lens Catalog MCP server.

Deterministic, LLM-free core (db / indexes / query) plus an optional, lazily-loaded
pipeline tool. Designed to be consumed by any LLM client (Claude, an ADK, the
multi-agent orchestrator) — the client supplies the reasoning; this package supplies
indexed, safe, schema-aware tools over the Supabase lens catalog.
"""
