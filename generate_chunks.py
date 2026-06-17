"""
generate_chunks.py
═══════════════════════════════════════════════════════════════════════════════════
Multi-Family Schema-RAG Chunk Generator for the EarthTekniks AI System.

Scans every .md documentation file in the docs/ directory, splits each file
by `# Table: <table_name>` headers, and produces one unified chunk per table.

Each chunk carries structured metadata (product_type, table_name, and optional
Line Scan fields like resolution_target / pixel_pitch_um) so ChromaDB can
pre-filter at retrieval time.

Output:
    chroma_chunks.json — ready for ingest_chroma.py (format unchanged)
═══════════════════════════════════════════════════════════════════════════════════
"""

import glob
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(SCRIPT_DIR, "docs")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "chroma_chunks.json")

# ═══════════════════════════════════════════════════════════════════════════════
# CENTRAL PRODUCT TYPE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════
# This is the SINGLE SOURCE OF TRUTH for mapping table names to product types.
# Every table that appears in documentation must have an entry here.
# To add a new product family, add the table name and its product type below.

PRODUCT_TYPE_REGISTRY = {
    # ── Line Scan ─────────────────────────────────────────────────────────
    "line_scan_lens_4k7u": "line_scan",
    "line_scan_lens_8k5u": "line_scan",
    "line_scan_lens_8k7u": "line_scan",
    "line_scan_lens_12k5u": "line_scan",
    "line_scan_lens_16k3_5u": "line_scan",
    "line_scan_lens_16k5u": "line_scan",
    "new_series_line_scan_lens_4k7u": "line_scan",
    "coaxial_illumination_line_scan_lens": "line_scan",
    "ultra_high_resolution_line_scan_lenses": "line_scan",
    # ── FA ────────────────────────────────────────────────────────────────
    "fa_lenses": "fa_lens",
    # ── Telecentric ───────────────────────────────────────────────────────
    "standard_telecentric_lenses_2_3_inch": "telecentric",
    "standard_telecentric_lenses_1_1_inch": "telecentric",
    "telecentric_lenses_65mp": "telecentric",
    "non_standard_telecentric_lenses": "telecentric",
    "motorized_bi_telecentric_lenses": "telecentric",
    # ── Macro ─────────────────────────────────────────────────────────────
    "macro_lenses": "macro",
    # ── Large Format ──────────────────────────────────────────────────────
    "large_format_lenses": "large_format",
    "large_format_autofocus_lenses": "large_format",
    # ── Zoom ──────────────────────────────────────────────────────────────
    "zoom_lenses": "zoom",
    # ── Microscope / Magnifying ───────────────────────────────────────────
    "microscope_lenses": "microscope",
    "magnifying_lenses": "microscope",
    # ── Spectral ──────────────────────────────────────────────────────────
    "spectral_lenses": "spectral",
    # ── Three-CMOS ────────────────────────────────────────────────────────
    "three_cmos_lenses": "three_cmos",
    # ── M12 Mount ─────────────────────────────────────────────────────────
    "m12_mount_lenses": "m12_mount",
    # ── Anti-Vibration ────────────────────────────────────────────────────
    "anti_vibration_lenses": "anti_vibration",
    # ── Autofocus ─────────────────────────────────────────────────────────
    "autofocus_lenses": "autofocus",
    # ── Laser Coaxial ─────────────────────────────────────────────────────
    "laser_coaxial_lenses": "laser_coaxial",
    # ── Inspection ────────────────────────────────────────────────────────
    "inspection_360_systems": "inspection",
    # ── Accessories ───────────────────────────────────────────────────────
    "adapters": "accessory",
    "extension_rings": "accessory",
    "focusing_rings": "accessory",
    "lens_holders": "accessory",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY-AWARE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════
# Base aliases are injected into EVERY chunk for broad semantic retrieval.
# Category-specific aliases are appended only for their product type.

BASE_ALIASES = [
    "focal length", "aperture", "F-number", "f-stop",
    "distortion", "warping", "magnification", "price", "cost",
    "weight", "mass", "size", "mount", "working distance",
    "WD", "standoff", "clearance", "model", "lens",
]

CATEGORY_ALIASES = {
    "line_scan": [
        "FOV", "field of view", "sensor coverage", "pixel pitch",
        "resolution", "illuminance", "uniformity", "line scan",
        "scan", "web inspection", "coaxial", "conjugate", "o_i",
        "track length", "brightness", "speed", "fast aperture", "low light",
    ],
    "fa_lens": [
        "factory automation", "FA", "sensor format", "image circle",
        "megapixel", "angle of view", "MOD", "minimum object distance",
        "infinity focus", "industrial",
    ],
    "telecentric": [
        "telecentric", "telecentricity", "depth of field", "DOF",
        "NA", "numerical aperture", "object resolution", "TTL",
        "bi-telecentric", "illumination type", "nd", "measurement",
    ],
    "macro": [
        "macro", "close-up", "object distance", "reproduction ratio",
        "high magnification", "close range",
    ],
    "large_format": [
        "large format", "large sensor", "high resolution",
        "megapixel", "wide coverage", "autofocus", "motorized",
    ],
    "zoom": [
        "zoom", "variable magnification", "zoom method", "motorized zoom",
        "manual zoom", "zoom ratio", "focus method",
    ],
    "microscope": [
        "microscope", "magnifying", "objective", "wavelength",
        "tube lens", "specimen", "micron", "NA", "numerical aperture",
    ],
    "spectral": [
        "spectral", "SWIR", "NIR", "wavelength", "hyperspectral",
        "multispectral", "infrared", "band", "coating",
    ],
    "three_cmos": [
        "three CMOS", "3-CMOS", "prism", "color separation",
        "RGB", "image resolution",
    ],
    "m12_mount": [
        "M12", "board lens", "miniature", "compact lens",
        "small form factor", "S-mount",
    ],
    "anti_vibration": [
        "anti-vibration", "vibration resistant", "shake",
        "stabilization", "industrial vibration",
    ],
    "autofocus": [
        "autofocus", "AF", "motorized focus", "auto-focus",
        "motor", "controller", "speed", "precision", "response time",
    ],
    "laser_coaxial": [
        "laser", "coaxial laser", "laser alignment",
        "structured light", "laser illumination",
    ],
    "inspection": [
        "360 inspection", "360", "cylindrical inspection",
        "bottle inspection", "tube inspection", "ring light",
    ],
    "accessory": [
        "adapter", "extension ring", "focusing ring", "lens holder",
        "mount conversion", "spacer", "tube", "ring",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# METADATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_table_metadata(table_name: str) -> dict:
    """Build structured metadata for a table chunk.

    Always includes table_name and product_type.
    Line Scan tables additionally get resolution_target, pixel_pitch_um,
    is_coaxial, and is_new_series for backward-compatible filtering.
    """
    product_type = PRODUCT_TYPE_REGISTRY.get(table_name, "unknown")

    meta = {
        "table_name": table_name,
        "product_type": product_type,
    }

    # ── Line Scan specific fields (backward compat) ───────────────────
    if product_type == "line_scan":
        res_match = re.search(r'(\d+)k', table_name)
        if res_match:
            meta["resolution_target"] = f"{res_match.group(1)}K"

        pitch_match = re.search(r'(\d+(?:_\d+)?)u', table_name)
        if pitch_match:
            meta["pixel_pitch_um"] = float(pitch_match.group(1).replace('_', '.'))

        if "coaxial" in table_name:
            meta["is_coaxial"] = True

        if "new_series" in table_name:
            meta["is_new_series"] = True

    return meta


def get_aliases(product_type: str) -> list:
    """Return combined base + category-specific aliases."""
    return BASE_ALIASES + CATEGORY_ALIASES.get(product_type, [])


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PARSER (MULTI-FILE, UNIFIED CHUNKING)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_chunks():
    """Scan all .md files in docs/, split by # Table: headers, emit one
    chunk per table with enriched metadata.

    Output format is identical to the previous single-file version so
    ingest_chroma.py requires zero changes.
    """
    if not os.path.isdir(DOCS_DIR):
        print(f"ERROR: docs/ directory not found at {DOCS_DIR}")
        print("Create it and add your documentation .md files.")
        return

    md_files = sorted(glob.glob(os.path.join(DOCS_DIR, "*.md")))
    if not md_files:
        print(f"ERROR: No .md files found in {DOCS_DIR}")
        return

    print(f"Scanning {len(md_files)} documentation files in docs/...\n")

    final_chunks = []
    seen_tables = set()

    for md_file in md_files:
        filename = os.path.basename(md_file)
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by # Table: headers (same regex as original)
        table_blocks = re.split(r'\n# Table:\s*', '\n' + content)[1:]

        if not table_blocks:
            print(f"  ⚠️  {filename}: No '# Table:' headers found — skipped")
            continue

        for block in table_blocks:
            lines = block.split('\n')
            table_name = lines[0].strip()

            if not table_name:
                continue

            if table_name in seen_tables:
                print(f"  ⚠️  Duplicate table '{table_name}' in {filename} — skipped")
                continue
            seen_tables.add(table_name)

            # Build metadata
            meta = extract_table_metadata(table_name)
            product_type = meta["product_type"]

            # Get category-aware aliases
            aliases = get_aliases(product_type)
            meta["aliases"] = aliases
            meta["chunk_type"] = "table_unified_schema"

            # Build the chunk text (same format as original)
            aliases_text = "Universal Engineering Aliases: " + ", ".join(aliases) + "\n\n"
            full_text = f"[Table: {table_name}]\n{aliases_text}{block}"

            final_chunks.append({
                "id": f"chunk_{table_name}_unified",
                "text": full_text,
                "metadata": meta
            })

        tables_in_file = [c["metadata"]["table_name"] for c in final_chunks
                          if c["metadata"]["table_name"] in
                          {lines.split('\n')[0].strip()
                           for b in table_blocks
                           if (lines := b)}]
        print(f"  ✅ {filename}: {len(table_blocks)} table(s)")

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"Total chunks generated: {len(final_chunks)}")

    # Group by product_type for summary
    type_counts = {}
    for chunk in final_chunks:
        pt = chunk["metadata"]["product_type"]
        type_counts[pt] = type_counts.get(pt, 0) + 1
    for pt, count in sorted(type_counts.items()):
        print(f"  {pt:.<30} {count} table(s)")

    # Warn about unknown product types
    unknowns = [c["metadata"]["table_name"] for c in final_chunks
                if c["metadata"]["product_type"] == "unknown"]
    if unknowns:
        print(f"\n⚠️  Tables with unknown product_type (add to PRODUCT_TYPE_REGISTRY):")
        for t in unknowns:
            print(f"   - {t}")

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=4)

    print(f"\n✅ Wrote {len(final_chunks)} chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_chunks()