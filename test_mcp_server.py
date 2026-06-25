"""
test_mcp_server.py
═════════════════════════════════════════════════════════════════════════════════
Smoke test for the deterministic MCP tools against the live catalog DB.
Run:  python test_mcp_server.py
(No pytest dependency; plain asserts + a summary line.)
═════════════════════════════════════════════════════════════════════════════════
"""
from etk_mcp import indexes, query


def main():
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))
        print(f"  {'✅' if cond else '❌'} {name}")

    # Indexes (no DB)
    check("list_families returns families", len(indexes.list_families()) > 0)
    check("lookup_model exact (FA0401C)",
          indexes.find_model("FA0401C")["matches"][0]["table"] == "fa_lenses")
    check("lookup_model fuzzy (mv1105 -> MV11051*)",
          any(m["model_name"].startswith("MV1105")
              for m in indexes.find_model("mv1105").get("suggestions", [])))
    check("describe_table surfaces unit caveat (three_cmos metres)",
          "METRES" in indexes.describe_table("three_cmos_lenses")["notes"])

    # Query layer (DB)
    cheapest = query.find_extreme("list_price", "all", "min")
    check("find_extreme cheapest-overall returns a row", cheapest.get("row_count") == 1)

    dof = query.search_products(family="telecentric",
                                filters=[{"column": "dof_mm", "op": ">", "value": 5}],
                                columns=["dof_mm"], limit=20)
    check("search_products telecentric dof>5 spans multiple tables",
          len(dof.get("tables_searched", [])) > 1 and dof.get("row_count", 0) > 0)

    blocked = query.run_select("UPDATE fa_lenses SET list_price = 0;")
    check("run_select blocks writes", "error" in blocked)

    ok = query.run_select(
        "SELECT model_name, list_price FROM fa_lenses WHERE list_price IS NOT NULL "
        "ORDER BY list_price ASC LIMIT 1;")
    check("run_select runs a valid SELECT", ok.get("row_count") == 1)

    prod = query.get_product("FA0401C")
    check("get_product returns a row for FA0401C",
          prod["results"] and prod["results"][0]["row"] is not None)

    passed = sum(1 for _, ok in checks if ok)
    print(f"\n  {passed}/{len(checks)} checks passed")
    return passed == len(checks)


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
