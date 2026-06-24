"""
build_model_index.py
═════════════════════════════════════════════════════════════════════════════════
Build the MODEL INDEX: a mapping from every `model_name` in the catalog to the
table (and product family) that contains it.

This is the primitive that lets the SQL Agent answer bare model-name queries like
"MV11051B fov?" — without it, there is no way to know which of the ~38 tables holds
a given model, so such queries cannot be routed.

What it does:
  1. Read schema_registry.json to get every table that has a `model_name` column.
  2. SELECT model_name from each table (read-only).
  3. Map each model to its table + product_type (from PRODUCT_TYPE_REGISTRY).
  4. Write model_index.json.

Run this once, and again whenever the Supabase data is re-ingested.

Usage:
    python build_model_index.py
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os

from pipeline import execute_sql_safely, normalize_model_key
from generate_chunks import PRODUCT_TYPE_REGISTRY

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_REGISTRY_PATH = os.path.join(SCRIPT_DIR, "schema_registry.json")
MODEL_INDEX_PATH = os.path.join(SCRIPT_DIR, "model_index.json")


def build_model_index() -> dict:
    """Scan every model-bearing table and build the model → table index.

    Returns a dict keyed by normalized model name. Because the same model_name
    could (in principle) appear in more than one table, each value is a LIST of
    {model_name, table, product_type} entries.
    """
    with open(SCHEMA_REGISTRY_PATH, "r") as f:
        schema_registry = json.load(f)

    index: dict[str, list] = {}
    total_models = 0
    tables_scanned = 0
    tables_skipped = []

    for table, columns in schema_registry.items():
        if "model_name" not in columns:
            tables_skipped.append((table, "no model_name column"))
            continue

        product_type = PRODUCT_TYPE_REGISTRY.get(table, "unknown")

        df, error = execute_sql_safely(f"SELECT model_name FROM {table};")
        if error:
            tables_skipped.append((table, f"query error: {error[:80]}"))
            print(f"  ⚠️  {table}: {error[:120]}")
            continue

        tables_scanned += 1
        n = 0
        for raw in df["model_name"].dropna().tolist():
            model_name = str(raw).strip()
            if not model_name:
                continue
            key = normalize_model_key(model_name)
            entry = {
                "model_name": model_name,
                "table": table,
                "product_type": product_type,
            }
            index.setdefault(key, [])
            # Avoid exact-duplicate entries (same model in same table listed twice)
            if entry not in index[key]:
                index[key].append(entry)
            n += 1
        total_models += n
        print(f"  ✅ {table:<42} {n:>4} models  ({product_type})")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  Tables scanned : {tables_scanned}")
    print(f"  Unique keys    : {len(index)}")
    print(f"  Total models   : {total_models}")

    # Flag any model that resolves to more than one table (ambiguous routing)
    collisions = {k: v for k, v in index.items() if len(v) > 1}
    if collisions:
        print(f"\n  ⚠️  {len(collisions)} model name(s) appear in multiple tables:")
        for k, entries in list(collisions.items())[:20]:
            tbls = ", ".join(e["table"] for e in entries)
            print(f"      {entries[0]['model_name']}  →  {tbls}")

    if tables_skipped:
        print(f"\n  Skipped tables:")
        for t, why in tables_skipped:
            print(f"      {t}: {why}")

    return index


if __name__ == "__main__":
    print(f"\n{'═' * 60}")
    print(f"  🔑  BUILDING MODEL INDEX")
    print(f"{'═' * 60}")
    idx = build_model_index()
    with open(MODEL_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    print(f"\n  📁 Wrote model index to: {MODEL_INDEX_PATH}")
    print(f"{'═' * 60}\n")
