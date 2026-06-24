"""
column_aliases.py
═════════════════════════════════════════════════════════════════════════════════
Alias / synonym / unit map for the lens catalog (Phase 3 groundwork).

The Supabase schema is internally inconsistent: the SAME concept is spelled
differently across tables (e.g. `sensor_size_raw` vs `sensor_raw`), and a few
columns use different UNITS than their counterparts elsewhere (e.g.
`three_cmos_lenses.wd_*_m` is in METRES while every other table's working
distance is in millimetres).

Rather than rename columns in the live database (risky, high blast radius), we
keep the DB + `schema_registry.json` as the accurate source of truth and teach
the SQL generator about the inconsistencies here. `build_context_notes(tables)`
emits a short prompt block describing the synonyms and unit caveats relevant to
the tables actually in play for a query.

This is intentionally data-driven — add an entry to extend coverage.
═════════════════════════════════════════════════════════════════════════════════
"""

# ── Concept → the differently-named columns that mean the same thing ────────────
# Same meaning AND same unit; only the column name differs across tables.
COLUMN_SYNONYMS = {
    "sensor size (raw text)":      ["sensor_size_raw", "sensor_raw"],
    "flange distance (mm)":        ["flange_distance", "flange_distance_mm"],
    "total track length / TTL (mm, single value)": ["ttl", "ttl_mm"],
}

# ── Per-table UNIT caveats ──────────────────────────────────────────────────────
# These columns deviate from the unit used for the same concept in other tables.
# Each note is injected ONLY when its table is in the query context.
TABLE_UNIT_CAVEATS = {
    "three_cmos_lenses": [
        "Working distance columns `wd_min_m` / `wd_max_m` are in METRES (m), "
        "NOT millimetres. Every other table stores working distance in mm. "
        "To compare or filter against a value given in mm, multiply these by 1000 "
        "(or divide the user's mm value by 1000).",
    ],
    "microscope_lenses": [
        "Depth of field `dof_um` is in MICRONS (µm), not millimetres. Other tables "
        "use `dof_mm`. Convert if comparing across tables (1 mm = 1000 µm).",
    ],
}


def build_context_notes(tables: list) -> str:
    """Build a prompt block of alias + unit notes relevant to `tables`.

    Returns an empty string when nothing relevant applies (so the prompt stays
    clean for the common case). Otherwise returns a block ending in two newlines,
    ready to splice into the SQL-generation system prompt.
    """
    tables = [t for t in dict.fromkeys(tables) if t]  # dedupe, drop falsy, keep order
    if not tables:
        return ""

    lines = []

    # Unit caveats for the specific tables in context (correctness-critical)
    unit_lines = []
    for t in tables:
        for note in TABLE_UNIT_CAVEATS.get(t, []):
            unit_lines.append(f"- [{t}] {note}")
    if unit_lines:
        lines.append("UNIT CAVEATS (apply these exactly):")
        lines.extend(unit_lines)

    # Synonym reminder: only mention pairs whose columns could appear in these
    # tables, so the generator knows the alternate spellings refer to one concept.
    syn_lines = []
    for concept, variants in COLUMN_SYNONYMS.items():
        syn_lines.append(f"- {concept}: {' = '.join(variants)} (use the one present in the table's schema)")
    if syn_lines:
        lines.append("COLUMN NAME SYNONYMS (same meaning, spelling differs by table):")
        lines.extend(syn_lines)

    return "\n".join(lines) + "\n\n" if lines else ""
