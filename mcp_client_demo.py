"""
mcp_client_demo.py
═════════════════════════════════════════════════════════════════════════════════
Connect to a RUNNING EarthTekniks MCP server and call its tools — the way a real
client (Claude / orchestrator) would, over the wire.

Usage:
    # Terminal 1: start the server over HTTP
    python server.py --http

    # Terminal 2: run this client
    python mcp_client_demo.py                       # runs the demo calls
    python mcp_client_demo.py http://127.0.0.1:8765/mcp   # custom URL
═════════════════════════════════════════════════════════════════════════════════
"""
import asyncio
import os
import sys

from fastmcp import Client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp"
# Bearer token if the server requires auth (set the same ETK_MCP_TOKEN it uses).
TOKEN = os.getenv("ETK_MCP_TOKEN", "").strip() or None

DEMO_CALLS = [
    ("list_families", {}),
    ("lookup_model", {"name": "FA0401C"}),
    ("find_extreme", {"metric": "list_price", "scope": "all", "direction": "min"}),
    ("search_products", {
        "family": "macro",
        "filters": [{"column": "magnification_max", "op": ">", "value": 1}],
        "columns": ["magnification_max"],
    }),
    ("run_select", {
        "sql": "SELECT model_name, weight_g FROM fa_lenses "
               "WHERE weight_g IS NOT NULL ORDER BY weight_g ASC LIMIT 3;"
    }),
]


async def main():
    print(f"Connecting to {URL} ...\n")
    async with Client(URL, auth=TOKEN) as client:
        tools = await client.list_tools()
        print("✅ Connected. Tools available:")
        for t in tools:
            print(f"   • {t.name}")
        print()
        for name, args in DEMO_CALLS:
            result = await client.call_tool(name, args)
            data = result.data
            # Trim big payloads for readability
            if isinstance(data, dict) and "rows" in data:
                data = {"row_count": data.get("row_count"), "rows": data.get("rows")}
            print(f"▶ {name}({args})")
            print(f"   → {data}\n")


if __name__ == "__main__":
    asyncio.run(main())
