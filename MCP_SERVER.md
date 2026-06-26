# EarthTekniks Lens Catalog — MCP Server

A decoupled, **use-case-agnostic** MCP server that exposes the lens catalog as tools
for any LLM client — Claude (Agent SDK / Desktop), an ADK, or the multi-agent
orchestrator. The **client supplies the reasoning**; this server supplies indexed,
safe, schema-aware tools over the Supabase catalog.

It is **separate from the standalone agent** (`mvp_api.py` etc.) and reuses only the
*deterministic* pieces (`sql_validator.py`, `multi_table.py`, `column_aliases.py`,
and the JSON indexes). The deterministic core has **no Ollama/ChromaDB dependency**.

## Architecture

```
LLM client (Claude / orchestrator)
        │  calls tools
        ▼
server.py  (FastMCP)
        │
        ├─ etk_mcp/indexes.py   in-memory model/schema/catalog indexes (no DB hits)
        ├─ etk_mcp/query.py     structured search · cross-table superlatives · validated SELECT
        ├─ etk_mcp/db.py        read-only psycopg2 · timeout · row cap · TTL cache
        └─ etk_mcp/pipeline_tool.py   OPTIONAL local-LLM pipeline (ETK_ENABLE_PIPELINE_TOOL=1)
```

## Tools

Deterministic (always on, no LLM):

| Tool | Purpose |
|------|---------|
| `list_families()` | families + their tables (from index, no DB) |
| `list_tables(family?)` | tables + one-line purpose |
| `describe_table(table)` | columns, purpose, **unit/synonym caveats** (e.g. three_cmos WD in metres) |
| `lookup_model(name)` | model name → table/family (exact + fuzzy, no DB) |
| `get_product(model_name)` | full spec row(s) for a model |
| `search_products(table\|family, filters, columns, sort, limit)` | structured filtered search (whitelisted columns) |
| `find_extreme(metric, scope, direction, limit)` | cross-table superlatives (cheapest/heaviest/widest…) |
| `run_select(sql)` | client-written SELECT, validated read-only + grounded, row-capped |

Optional (`ETK_ENABLE_PIPELINE_TOOL=1`, needs Ollama): `query_catalog(request, history?)`
— delegate a whole NL request to the local pipeline.

## Setup

```bash
pip install -r requirements-mcp.txt    # deterministic core
```
Requires the same `.env` as the rest of the project (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, …).
Loads `model_index.json` / `schema_registry.json` / `table_catalog.json` (committed).

## Run

```bash
python server.py                 # stdio  (Claude Desktop, MCP Inspector)
python server.py --http          # streamable HTTP on http://127.0.0.1:8765/mcp
python server.py --http --port 9000 --host 0.0.0.0
```

Optional config: `ETK_ROW_CAP`, `ETK_STATEMENT_TIMEOUT_MS`, `ETK_CACHE_TTL_S`,
`ETK_ENABLE_PIPELINE_TOOL`.

## Connect to Claude Desktop (stdio)

Add to `claude_desktop_config.json` (use absolute paths):

```json
{
  "mcpServers": {
    "earthtekniks-lenses": {
      "command": "/ABS/PATH/schema-rag-eval/venv/bin/python",
      "args": ["/ABS/PATH/schema-rag-eval/server.py"]
    }
  }
}
```
Then ask Claude e.g. *"what's the cheapest lens overall?"* — it will call `find_extreme`.

## Inspect / test

```bash
python test_mcp_server.py    # deterministic-tool smoke test vs live DB
```

Quick programmatic check over the **real MCP protocol** (in your venv — recommended):

```python
import asyncio
from fastmcp import Client
import server

async def main():
    async with Client(server.mcp) as c:          # in-memory transport
        print([t.name for t in await c.list_tools()])
        r = await c.call_tool("find_extreme",
                {"metric": "list_price", "scope": "all", "direction": "min"})
        print(r.data["rows"])

asyncio.run(main())
```

Interactive MCP Inspector UI — point it at **your venv's python** (needs Node/npx),
bypassing the FastMCP CLI's own environment management:

```bash
npx @modelcontextprotocol/inspector venv/bin/python server.py
```

> Note: `fastmcp dev inspector server.py` runs the server in an isolated `uv`
> environment that won't have this project's deps. If you use it, pass
> `--with-requirements requirements-mcp.txt`. The in-memory `Client` above and the
> Inspector-via-npx command are simpler because they use your existing venv.

## Public exposure (Cloudflare Tunnel)

Expose the local HTTP server to the internet with a Cloudflare **quick tunnel** —
no Cloudflare account or domain needed.

```bash
# Terminal 1: run the server over HTTP
python server.py --http --port 8765

# Terminal 2: open a public tunnel to it
cloudflared tunnel --url http://localhost:8765
#   → prints  https://<random>.trycloudflare.com
```

Clients then connect to `https://<random>.trycloudflare.com/mcp`. Test it:
```bash
python mcp_client_demo.py https://<random>.trycloudflare.com/mcp
```

Caveats of a **quick** tunnel:
- The URL is **ephemeral** — it changes every time `cloudflared` restarts. For a
  **stable** URL you need a named tunnel: a free Cloudflare account + a domain, then
  `cloudflared tunnel create <name>` + a DNS route (see Cloudflare docs).
- The endpoint is **unauthenticated** by default. To require a bearer token, set
  `ETK_MCP_TOKEN=<secret>` before starting the server (the server enables
  `StaticTokenVerifier` automatically); clients pass the same token. Strongly
  recommended for anything beyond quick testing.

Optional auth, for reference:
```bash
ETK_MCP_TOKEN=my-secret python server.py --http      # server requires the token
ETK_MCP_TOKEN=my-secret python mcp_client_demo.py <url>   # client sends it
```

Stop everything:
```bash
pkill -f "cloudflared tunnel"
lsof -ti :8765 | xargs kill
```

## Safety
Read-only psycopg2 session; `SQLValidator` blocks writes/DDL and ungrounded
tables/columns on `run_select`; structured tools build SQL from whitelisted columns
only; every query is `statement_timeout`-bounded and row-capped.
