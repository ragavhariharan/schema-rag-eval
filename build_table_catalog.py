"""
build_table_catalog.py
═════════════════════════════════════════════════════════════════════════════════
Build the TABLE CATALOG: one compact entry per table for the Phase 2 router.

The router needs a small, in-prompt-able summary of every table so it can pick
the right table(s) for a query that names neither a model (Phase 1 handles that)
nor is reliably caught by the family keyword path. 32 tables × a one-line purpose
+ a few distinctive columns fits comfortably in the local model's context.

Each entry:
  {
    "family": "<product_type>",
    "purpose": "<first sentence of the docs ## Purpose section>",
    "signature_columns": ["<distinctive columns that hint at this table>", ...]
  }

Sources:
  - docs/*.md            → human-written purpose text
  - schema_registry.json → column lists (to compute distinctive columns)
  - generate_chunks.PRODUCT_TYPE_REGISTRY → table → family

Output: table_catalog.json   (committed; rebuild when docs/registry change)

Usage:
    python build_table_catalog.py
═════════════════════════════════════════════════════════════════════════════════
"""
import glob
import json
import os
import re
from collections import Counter

from generate_chunks import PRODUCT_TYPE_REGISTRY

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "docs")
SCHEMA_REGISTRY_PATH = os.path.join(SCRIPT_DIR, "schema_registry.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "table_catalog.json")

# Columns common to almost every table — not useful as routing signal.
GENERIC_COLUMNS = {
    "model_name", "list_price", "price_usd", "weight_g", "mount_raw",
    "size_raw", "size_diameter_mm", "size_length_mm", "size_length_min_mm",
    "size_length_max_mm", "flange_distance", "filter_thread_raw",
    "focus_length_mm", "f_no_raw", "f_no_min", "f_no_max",
    "tv_distortion_operator", "tv_distortion_percent",
}

# How rare a column must be (≤ this many tables) to count as "distinctive".
DISTINCTIVE_MAX_TABLES = 8
MAX_SIGNATURE_COLUMNS = 12


def extract_purpose(block: str) -> str:
    """Pull a one-line purpose from a table's docs block (text under ## Purpose)."""
    m = re.search(r"##\s*Purpose\s*(.+?)(?:\n#{1,2}\s|\n---)", block, re.DOTALL)
    if not m:
        return ""
    text = m.group(1).strip()
    text = text.replace("**", "")              # drop markdown bold
    text = re.sub(r"\s+", " ", text)            # collapse whitespace
    # First sentence (up to the first period followed by a space + capital, or end)
    sentence = re.split(r"(?<=\.)\s+(?=[A-Z])", text)[0]
    return sentence.strip()


def parse_docs_purposes() -> dict:
    """table_name → purpose sentence, scanned from every docs/*.md file."""
    purposes = {}
    for md in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        content = open(md, encoding="utf-8").read()
        blocks = re.split(r"\n# Table:\s*", "\n" + content)[1:]
        for block in blocks:
            table = block.split("\n", 1)[0].strip()
            if table and table not in purposes:
                purposes[table] = extract_purpose(block)
    return purposes


def build_catalog() -> dict:
    registry = json.load(open(SCHEMA_REGISTRY_PATH))
    purposes = parse_docs_purposes()

    # Column frequency across all tables → identifies distinctive columns
    freq = Counter()
    for cols in registry.values():
        for c in set(cols):
            freq[c] += 1

    catalog = {}
    for table, cols in registry.items():
        distinctive = [
            c for c in cols
            if c not in GENERIC_COLUMNS
            and not c.endswith("_operator")
            and freq[c] <= DISTINCTIVE_MAX_TABLES
        ]
        catalog[table] = {
            "family": PRODUCT_TYPE_REGISTRY.get(table, "unknown"),
            "purpose": purposes.get(table, ""),
            "signature_columns": distinctive[:MAX_SIGNATURE_COLUMNS],
        }
        if not purposes.get(table):
            print(f"  ⚠️  no Purpose text found for {table}")

    return catalog


if __name__ == "__main__":
    print(f"\n{'═' * 60}\n  📚  BUILDING TABLE CATALOG\n{'═' * 60}")
    cat = build_catalog()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2, ensure_ascii=False)
    print(f"\n  Tables: {len(cat)}")
    print(f"  📁 Wrote catalog to: {OUTPUT_PATH}\n{'═' * 60}\n")
