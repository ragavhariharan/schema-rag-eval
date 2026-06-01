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

def get_aliases(group_type, title=""):
    """Injects lexical synonyms for BM25/Hybrid Search robustness."""
    if group_type == "optical_core":
        # Added "warping" to optical core synonyms
        return ["focal length", "aperture", "F-number", "f-stop", "distortion", "warping", "FOV", "field of view", "magnification", "brightness", "speed"]
    elif group_type == "conjugate_mount":
        return ["WD", "standoff", "clearance", "working distance", "track length", "conjugate", "mount", "thread", "flange"]
    elif group_type == "dimensions":
        return ["price", "cost", "weight", "mass", "diameter", "width", "size", "length", "compact", "heavy"]
    elif group_type == "sql_example":
        title_lower = title.lower()
        if "working distance" in title_lower:
            return ["WD", "standoff", "clearance"]
        elif "compatibility" in title_lower:
            return ["fit", "mount", "sensor coverage", "thread"]
        elif "ambiguous" in title_lower:
            # Added "warping" to ambiguous terminology synonyms
            return ["distortion", "warping", "illuminance", "o_i", "flange"]
        elif "filtering" in title_lower:
            return ["fast aperture", "low light", "uniformity"]
    return []

# ==========================================
# MAIN PARSER
# ==========================================
def generate_chunks():
    with open("line_scan_documentation.md", "r", encoding="utf-8") as f:
        content = f.read()

    final_chunks = []
    table_blocks = re.split(r'\n# Table:\s*', '\n' + content)[1:]

    for block in table_blocks:
        table_name = block.split('\n')[0].strip()
        
        # 1. Get explicit engineering metadata for this table
        engineering_meta = extract_lens_metadata(table_name)
        
        attributes_section = re.search(r'## Attributes\n(.*?)(?=\n##|$)', block, re.DOTALL)
        if attributes_section:
            optical_core = []
            conjugate_mount = []
            dimensions = []
            
            rows = re.findall(r'\|\s*([a-z0-9_]+)\s*\|\s*(.*?)\s*\|', attributes_section.group(1))
            
            for col_name, col_desc in rows:
                col_name = col_name.strip()
                row_text = f"{col_name}: {col_desc.strip()}"
                
                if col_name in ["focus_length_mm", "f_no_min", "f_no_max", "tv_distortion_percent", "relative_illuminance_percent", "fov_degrees", "fov_mm", "magnification_min", "magnification_max"]:
                    optical_core.append(row_text)
                elif col_name in ["wd_mm", "o_i", "flange_distance", "mount_raw", "filter_thread_raw"]:
                    conjugate_mount.append(row_text)
                elif col_name in ["weight_g", "size_diameter_mm", "size_length_min_mm", "size_length_mm", "list_price"]:
                    dimensions.append(row_text)

            # Generate Attribute Chunks with enriched metadata
            if optical_core:
                aliases_list = get_aliases("optical_core")
                meta = {"parent_table": table_name, "chunk_type": "attribute_group", "semantic_group": "optical_core", "aliases": aliases_list}
                meta.update(engineering_meta)
                final_chunks.append({
                    "id": f"chunk_{table_name}_optical",
                    "text": f"[Table: {table_name}] Optical Attributes (aliases/synonyms: {', '.join(aliases_list)}): " + " | ".join(optical_core),
                    "metadata": meta
                })
            if conjugate_mount:
                aliases_list = get_aliases("conjugate_mount")
                meta = {"parent_table": table_name, "chunk_type": "attribute_group", "semantic_group": "conjugate_mount", "aliases": aliases_list}
                meta.update(engineering_meta)
                final_chunks.append({
                    "id": f"chunk_{table_name}_conjugate",
                    "text": f"[Table: {table_name}] Conjugate & Mount Attributes (aliases/synonyms: {', '.join(aliases_list)}): " + " | ".join(conjugate_mount),
                    "metadata": meta
                })
            if dimensions:
                aliases_list = get_aliases("dimensions")
                meta = {"parent_table": table_name, "chunk_type": "attribute_group", "semantic_group": "dimensions", "aliases": aliases_list}
                meta.update(engineering_meta)
                final_chunks.append({
                    "id": f"chunk_{table_name}_dimensions",
                    "text": f"[Table: {table_name}] Dimension Attributes (aliases/synonyms: {', '.join(aliases_list)}): " + " | ".join(dimensions),
                    "metadata": meta
                })

        queries_section = re.search(r'## Example Queries\n(.*?)(?=\n##|$)', block, re.DOTALL)
        if queries_section:
            query_blocks = re.split(r'\n\*\*\d+\.\s*(.*?)\*\*\n', '\n' + queries_section.group(1))[1:]
            
            for i in range(0, len(query_blocks), 2):
                title = query_blocks[i].strip()
                content_block = query_blocks[i+1]
                
                nl_match = re.search(r'Natural Language:\s*(.*?)\s*Reasoning:', content_block, re.DOTALL)
                reasoning_match = re.search(r'Reasoning:\s*(.*?)\s*```sql', content_block, re.DOTALL)
                sql_match = re.search(r'```sql\s*(.*?)\s*```', content_block, re.DOTALL)
                
                if nl_match and reasoning_match and sql_match:
                    nl_text = nl_match.group(1).strip()
                    reasoning_text = reasoning_match.group(1).replace('\n- ', ' ').replace('- ', '').strip()
                    sql_text = sql_match.group(1).strip()
                    
                    meta = {
                        "parent_table": table_name, 
                        "chunk_type": "sql_example", 
                        "contains_sql": True,
                        "aliases": get_aliases("sql_example", title)
                    }
                    meta.update(engineering_meta)
                    
                    final_chunks.append({
                        "id": f"chunk_{table_name}_sql_{len(final_chunks)}",
                        "text": f"[Table: {table_name}] Query Type: {title}. Natural Language: {nl_text} Engineering Reasoning: {reasoning_text} SQL: {sql_text}",
                        "metadata": meta
                    })

    with open("chroma_chunks.json", "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=4)

    print(f"Extraction Complete. Generated {len(final_chunks)} highly enriched semantic chunks.")

if __name__ == "__main__":
    generate_chunks()