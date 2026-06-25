"""
etk_mcp/indexes.py
═════════════════════════════════════════════════════════════════════════════════
In-memory indexes loaded once at import. Schema discovery and model-name resolution
are served entirely from these JSON files — they never touch the database.

  model_index.json     model_name → [{model_name, table, product_type}]
  schema_registry.json table → [columns]
  table_catalog.json   table → {family, purpose, signature_columns}

Reuses `column_aliases.build_context_notes` (deterministic) to surface unit/synonym
caveats in describe_table.
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os
import re

from column_aliases import build_context_notes

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name: str) -> dict:
    with open(os.path.join(_ROOT, name), "r", encoding="utf-8") as f:
        return json.load(f)


MODEL_INDEX = _load("model_index.json")
SCHEMA_REGISTRY = _load("schema_registry.json")
TABLE_CATALOG = _load("table_catalog.json")

_ALL_COLUMNS = {c for cols in SCHEMA_REGISTRY.values() for c in cols}
_MODEL_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-/.]{2,}")


def normalize_model_key(model_name: str) -> str:
    """Uppercase, whitespace-stripped key — matches the agent's model index keys."""
    return "".join(str(model_name).split()).upper()


# ── Schema discovery (no DB) ────────────────────────────────────────────────────

def list_families() -> list:
    """Lens families and the tables in each."""
    fams: dict = {}
    for table, entry in TABLE_CATALOG.items():
        fams.setdefault(entry.get("family", "unknown"), []).append(table)
    return [
        {"family": fam, "tables": sorted(tabs), "table_count": len(tabs)}
        for fam, tabs in sorted(fams.items())
    ]


def list_tables(family: str = None) -> list:
    """Tables (optionally filtered to a family) with their one-line purpose."""
    out = []
    for table, entry in TABLE_CATALOG.items():
        if family and entry.get("family") != family:
            continue
        out.append({
            "table": table,
            "family": entry.get("family"),
            "purpose": entry.get("purpose", ""),
        })
    return out


def describe_table(table: str) -> dict:
    """Columns, purpose, signature columns, and unit/synonym caveats for a table."""
    if table not in SCHEMA_REGISTRY:
        return {"error": f"Unknown table '{table}'. Call list_tables() for valid names."}
    cat = TABLE_CATALOG.get(table, {})
    notes = build_context_notes([table]).strip()
    return {
        "table": table,
        "family": cat.get("family"),
        "purpose": cat.get("purpose", ""),
        "columns": SCHEMA_REGISTRY[table],
        "signature_columns": cat.get("signature_columns", []),
        "notes": notes,
    }


# ── Model resolution (no DB) ────────────────────────────────────────────────────

def find_model(name: str) -> dict:
    """Resolve a model name (exact, then token scan, then partial suggestions)."""
    key = normalize_model_key(name)
    if key in MODEL_INDEX:
        return {"query": name, "matches": MODEL_INDEX[key]}

    matches, seen = [], set()
    for tok in _MODEL_TOKEN_RE.findall(name):
        for entry in MODEL_INDEX.get(normalize_model_key(tok), []):
            sig = (entry["model_name"], entry["table"])
            if sig not in seen:
                seen.add(sig)
                matches.append(entry)
    if matches:
        return {"query": name, "matches": matches}

    # Partial / fuzzy suggestions (e.g. "MV1105" → MV11051B)
    suggestions = []
    for k, entries in MODEL_INDEX.items():
        if len(key) >= 3 and (key in k or k in key):
            suggestions.extend(entries)
    return {"query": name, "matches": [], "suggestions": suggestions[:10]}


# ── Helpers used by the query layer ─────────────────────────────────────────────

def all_tables() -> list:
    return list(SCHEMA_REGISTRY.keys())


def tables_with(column: str) -> list:
    return [t for t, cols in SCHEMA_REGISTRY.items() if column in cols]


def tables_in_family(family: str) -> list:
    return [t["table"] for t in list_tables(family=family)]


def column_exists(column: str) -> bool:
    return column in _ALL_COLUMNS


def is_table(name: str) -> bool:
    return name in SCHEMA_REGISTRY
