import re
import json

# ==========================================
# METADATA ENRICHMENT HELPERS
# ==========================================
def extract_lens_metadata(table_name):
    """Parses the table name to extract hard engineering filters."""
    meta = {
        "lens_family": "line_scan",
        "resolution_target": None,
        "pixel_pitch_um": None,
        "is_coaxial": False,
        "is_new_series": False
    }
    
    if "coaxial" in table_name:
        meta["is_coaxial"] = True
    if "new_series" in table_name:
        meta["is_new_series"] = True
        
    # Extract resolution (e.g., 4k, 8k, 12k, 16k)
    res_match = re.search(r'(\d+)k', table_name)
    if res_match:
        meta["resolution_target"] = f"{res_match.group(1)}K"
        
    # Extract pixel pitch (e.g., 5u, 7u, 3_5u)
    pitch_match = re.search(r'(\d+(?:_\d+)?)u', table_name)
    if pitch_match:
        meta["pixel_pitch_um"] = float(pitch_match.group(1).replace('_', '.'))
        
    return meta

def get_all_aliases():
    """Returns all lexical synonyms for BM25/Hybrid Search robustness."""
    return [
        "focal length", "aperture", "F-number", "f-stop", "distortion", "warping", 
        "FOV", "field of view", "magnification", "brightness", "speed",
        "WD", "standoff", "clearance", "working distance", "track length", 
        "conjugate", "mount", "thread", "flange", "price", "cost", "weight", 
        "mass", "diameter", "width", "size", "length", "compact", "heavy",
        "fit", "sensor coverage", "illuminance", "o_i", "fast aperture", 
        "low light", "uniformity"
    ]

# ==========================================
# MAIN PARSER (UNIFIED CHUNKING)
# ==========================================
def generate_chunks():
    with open("line_scan_documentation.md", "r", encoding="utf-8") as f:
        content = f.read()

    final_chunks = []
    # Split the document by table headers
    table_blocks = re.split(r'\n# Table:\s*', '\n' + content)[1:]

    for block in table_blocks:
        lines = block.split('\n')
        table_name = lines[0].strip()
        
        # Get explicit engineering metadata for this table
        engineering_meta = extract_lens_metadata(table_name)
        
        # Inject Universal Aliases
        aliases = get_all_aliases()
        engineering_meta["aliases"] = aliases
        engineering_meta["parent_table"] = table_name
        engineering_meta["chunk_type"] = "table_unified_schema"

        # The chunk text is the full documentation block + the aliases
        aliases_text = "Universal Engineering Aliases: " + ", ".join(aliases) + "\n\n"
        full_text = f"[Table: {table_name}]\n{aliases_text}{block}"
        
        final_chunks.append({
            "id": f"chunk_{table_name}_unified",
            "text": full_text,
            "metadata": engineering_meta
        })

    with open("chroma_chunks.json", "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=4)

    print(f"Extraction Complete. Generated {len(final_chunks)} unified table chunks.")

if __name__ == "__main__":
    generate_chunks()