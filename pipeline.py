"""
pipeline.py
═════════════════════════════════════════════════════════════════════════════════
Core Text-to-SQL RAG pipeline for the EarthTekniks SQL Agent (SQA).

This module is the SINGLE SOURCE OF TRUTH for the runtime pipeline. It owns:
  - Database connection + safe read-only execution        (get_db_connection, execute_sql_safely)
  - ChromaDB schema-context retrieval                     (chroma_client, collection)
  - LLM metadata filter extraction                        (llm_extract_filters)
  - SQL generation with self-healing validation loop      (run_pipeline)

Production (`sql_agent.py`, `mvp_api.py`) and all evaluation/debug scripts
(`run_execution_accuracy.py`, `run_full_evaluation.py`, `run_safety_benchmark.py`,
`run_sql_agent_debug.py`) import from here. Previously this code lived inside
`run_execution_accuracy.py`, which forced production to depend on an eval script;
it now lives in this dedicated module.
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os
import re
import warnings

import chromadb
import ollama
import pandas as pd
import psycopg2
from dotenv import load_dotenv

from column_aliases import build_context_notes

# Suppress pandas warning about psycopg2 not being a SQLAlchemy connection.
# We intentionally use psycopg2 directly for lightweight read-only queries.
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=True)

OLLAMA_MODEL = "llama3.1:8b"
CHROMA_DB_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
CHROMA_COLLECTION = "lens_schema_rag"
MODEL_INDEX_PATH = os.path.join(SCRIPT_DIR, "model_index.json")

# Database connection parameters — pulled from individual .env variables
# to avoid URL-parsing issues with special characters in the password.
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "6543"),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "options": "-c search_path=ragav",
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_db_connection():
    """Establish a secure psycopg2 connection to the Supabase PostgreSQL
    database, scoped to the 'ragav' schema via connection-level options."""
    missing = [k for k in ("host", "user", "password") if not DB_CONFIG.get(k)]
    if missing:
        raise ValueError(
            f"Missing required DB env vars: {', '.join('DB_' + k.upper() for k in missing)}. "
            "Check your .env file."
        )

    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        options=DB_CONFIG["options"],
        connect_timeout=15,
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn

def execute_sql_safely(sql: str) -> tuple:
    """Open a fresh DB connection, execute a SQL query, close it, and return
    (dataframe, error_string).

    A fresh connection per query avoids the Supabase pooler killing idle
    connections while the LLM pipeline is thinking between queries.

    Returns:
        (pd.DataFrame, None)  on success
        (None, str)           on failure (error message)
    """
    conn = None
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# CHROMADB SCHEMA-CONTEXT RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════════

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_collection(name=CHROMA_COLLECTION)


# Valid product types that the LLM can extract (must match PRODUCT_TYPE_REGISTRY
# in generate_chunks.py and the metadata stored in ChromaDB).
VALID_PRODUCT_TYPES = {
    "line_scan", "fa_lens", "telecentric", "macro", "large_format",
    "zoom", "microscope", "spectral", "three_cmos", "m12_mount",
    "anti_vibration", "autofocus", "laser_coaxial", "inspection",
    "accessory",
}


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL-NAME RESOLUTION  (Phase 1)
# ═══════════════════════════════════════════════════════════════════════════════
# Maps a model number named in a query (e.g. "MV11051B") to the table that holds
# it, so bare model-name queries can be routed directly instead of guessed via
# semantic search. Backed by model_index.json (built by build_model_index.py).
# Exact, whitespace/case-insensitive matching only — fuzzy matching is a later step.

_model_index = None


def normalize_model_key(model_name: str) -> str:
    """Normalize a model name into a lookup key: uppercase, no whitespace.
    Makes 'mv11051b', 'MV11051B', and 'MV 11051B' collide to the same key."""
    return "".join(str(model_name).split()).upper()


def _load_model_index() -> dict:
    """Lazily load model_index.json. Returns {} if it hasn't been built yet, so
    the pipeline degrades gracefully to the legacy family-routing path."""
    global _model_index
    if _model_index is None:
        try:
            with open(MODEL_INDEX_PATH, "r", encoding="utf-8") as f:
                _model_index = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _model_index = {}
    return _model_index


# Candidate model tokens contain a letter AND a digit (e.g. MV11051B, FA0401C).
# Spec tokens like "12K"/"65MP" may also match the regex, but they are harmless:
# a token only routes if it is an actual key in the model index.
_MODEL_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-/.]{2,}")


def resolve_models(user_query: str) -> list:
    """Find model numbers in the query that exist in the model index.

    Returns a list of {model_name, table, product_type} entries (deduplicated),
    in the order the models appear in the query. Empty list if none match.
    """
    index = _load_model_index()
    if not index:
        return []

    matches = []
    seen = set()
    for tok in _MODEL_TOKEN_RE.findall(user_query):
        # Must look like a model number: contain both a letter and a digit.
        if not (any(c.isalpha() for c in tok) and any(c.isdigit() for c in tok)):
            continue
        key = normalize_model_key(tok)
        for entry in index.get(key, []):
            sig = (entry["model_name"], entry["table"])
            if sig not in seen:
                seen.add(sig)
                matches.append(entry)
    return matches


def _build_routing_hint(resolved: list) -> str:
    """Build an explicit routing instruction for the SQL generator when the user
    named specific model(s)."""
    lines = [
        "ROUTING (the user named specific model(s) — query ONLY these tables and "
        "filter by model_name):",
    ]
    for e in resolved:
        lines.append(f"- model_name = '{e['model_name']}'  →  table {e['table']}")
    lines.append(
        "Use `WHERE model_name = '<model>'` (or `model_name IN (...)` for several "
        "models in one table). If the requested models live in different tables, "
        "write one SELECT per table and combine them with UNION ALL."
    )
    return "\n".join(lines) + "\n\n"


def llm_extract_filters(user_query: str) -> dict:
    """Dynamically extract ChromaDB metadata filters from a user query using the LLM.

    Uses Ollama's JSON mode for structured output. Returns a dict with keys
    matching ChromaDB metadata fields. Values are None for unidentified filters.

    Extracts:
        - product_type: which lens family the user is asking about
        - resolution_target: Line Scan specific (4K, 8K, 12K, 16K)
        - pixel_pitch_um: Line Scan specific (3.5, 5.0, 7.0)
        - is_coaxial: Line Scan specific
        - is_new_series: Line Scan specific
    """
    system_prompt = """You are a metadata filter extractor for an industrial machine vision lens catalog.
The catalog contains many product families. Given a user's natural language query, extract metadata filters as JSON.

{
  "product_type": string or null,
  "resolution_target": string or null,
  "pixel_pitch_um": number or null,
  "is_coaxial": true/false or null,
  "is_new_series": true/false or null
}

PRODUCT TYPE MAPPING (use EXACTLY these values):
- "line_scan"       → line scan lens, line scan, web inspection lens
- "fa_lens"         → FA lens, factory automation lens, industrial lens
- "telecentric"     → telecentric lens, bi-telecentric, measurement lens
- "macro"           → macro lens, close-up lens
- "large_format"    → large format lens, large sensor lens
- "zoom"            → zoom lens, variable magnification lens
- "microscope"      → microscope lens, magnifying lens, microscope objective
- "spectral"        → spectral lens, SWIR lens, NIR lens, hyperspectral lens
- "three_cmos"      → 3-CMOS lens, three CMOS lens, prism lens
- "m12_mount"       → M12 lens, M12 mount lens, board lens, S-mount lens
- "anti_vibration"  → anti-vibration lens, vibration resistant lens
- "autofocus"       → autofocus lens, AF lens, motorized focus lens
- "laser_coaxial"   → laser coaxial lens, laser alignment lens
- "inspection"      → 360 inspection, cylindrical inspection, bottle inspection
- "accessory"       → adapter, extension ring, focusing ring, lens holder

RULES:
- Return ONLY the JSON object, nothing else.
- Use null for any filter you cannot confidently extract from the query.
- "product_type" must be one of the exact strings listed above, or null.
- "resolution_target" must always be uppercase with K suffix (e.g. "8K", not "8k"). Only applies to line scan lenses.
- "pixel_pitch_um" must be a number (e.g. 3.5, not "3.5u"). Only applies to line scan lenses.
- "is_coaxial": true ONLY if the query explicitly mentions "coaxial". Only applies to line scan lenses.
- "is_new_series": true ONLY if the query explicitly mentions "new series". Only applies to line scan lenses.
- If the query is general (e.g. "all lenses under 200g") without specifying a family, return all nulls.
- If the query mentions a specific family (e.g. "cheapest FA lens"), set product_type accordingly."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        format="json",
        options={"temperature": 0, "num_ctx": 8192},
    )

    try:
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError):
        return {
            "product_type": None, "resolution_target": None,
            "pixel_pitch_um": None, "is_coaxial": None, "is_new_series": None,
        }

    filters = {
        "product_type": None,
        "resolution_target": None,
        "pixel_pitch_um": None,
        "is_coaxial": None,
        "is_new_series": None,
    }

    # ── Product Type ──────────────────────────────────────────────────────
    if parsed.get("product_type") and isinstance(parsed["product_type"], str):
        pt = parsed["product_type"].lower().strip()
        if pt in VALID_PRODUCT_TYPES:
            filters["product_type"] = pt

    # ── Line Scan specific fields ─────────────────────────────────────────
    if parsed.get("resolution_target") and isinstance(parsed["resolution_target"], str):
        val = parsed["resolution_target"].upper().replace(" ", "")
        if not val.endswith("K"):
            val += "K"
        filters["resolution_target"] = val

    if parsed.get("pixel_pitch_um") is not None:
        try:
            filters["pixel_pitch_um"] = float(parsed["pixel_pitch_um"])
        except (ValueError, TypeError):
            pass

    if isinstance(parsed.get("is_coaxial"), bool):
        filters["is_coaxial"] = parsed["is_coaxial"]

    if isinstance(parsed.get("is_new_series"), bool):
        filters["is_new_series"] = parsed["is_new_series"]

    # ── Post-extraction cleanup ───────────────────────────────────────────
    # resolution_target, pixel_pitch_um, is_coaxial, and is_new_series ONLY
    # exist as metadata on line_scan chunks. If the query targets a different
    # product family, these fields would cause zero ChromaDB results.
    if filters["product_type"] is not None and filters["product_type"] != "line_scan":
        filters["resolution_target"] = None
        filters["pixel_pitch_um"] = None
        filters["is_coaxial"] = None
        filters["is_new_series"] = None

    return filters


def extract_sql_from_text(text: str) -> str:
    """Extract clean SQL from an LLM response that may contain markdown fences."""
    sql_match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
    generic_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()
    return text.strip()


def run_pipeline(user_query: str) -> tuple:
    """Run the full RAG pipeline: extract filters → retrieve chunks → generate SQL.
    Includes an SQL Safety Layer with a self-healing retry loop.

    Returns:
        (generated_sql, retrieved_contexts, extracted_filters)
    """
    # ── Phase 1: model-name routing ───────────────────────────────────────
    # If the query names specific model(s), route straight to their table(s)
    # instead of guessing the lens family via semantic search.
    resolved = resolve_models(user_query)

    if resolved:
        # Unique tables, preserving query order
        tables = []
        for e in resolved:
            if e["table"] not in tables:
                tables.append(e["table"])

        filters = {
            "product_type": None,
            "resolution_target": None,
            "pixel_pitch_um": None,
            "is_coaxial": None,
            "is_new_series": None,
            "resolved_models": [e["model_name"] for e in resolved],
        }

        where = (
            {"table_name": {"$in": tables}} if len(tables) > 1
            else {"table_name": tables[0]}
        )
        results = collection.query(
            query_texts=[user_query], n_results=len(tables), where=where
        )
        contexts = results["documents"][0] if results["documents"] else []
        routing_hint = _build_routing_hint(resolved)
        tables_in_context = tables

    else:
        # ── Legacy family-routing path (no specific model named) ──────────
        filters = llm_extract_filters(user_query)

        search_params = {"query_texts": [user_query], "n_results": 3}

        and_conditions = []
        # ── Product type filter (routes to the correct lens family) ───────
        if filters.get("product_type"):
            and_conditions.append({"product_type": filters["product_type"]})
        # ── Line Scan specific filters (backward compatible) ──────────────
        if filters.get("resolution_target"):
            and_conditions.append({"resolution_target": filters["resolution_target"]})
        if filters.get("pixel_pitch_um") is not None:
            and_conditions.append({"pixel_pitch_um": filters["pixel_pitch_um"]})
        if filters.get("is_coaxial") is True:
            and_conditions.append({"is_coaxial": True})
        if filters.get("is_new_series") is True:
            and_conditions.append({"is_new_series": True})

        if and_conditions:
            search_params["where"] = (
                {"$and": and_conditions} if len(and_conditions) > 1 else and_conditions[0]
            )

        results = collection.query(**search_params)
        contexts = results["documents"][0] if results["documents"] else []
        routing_hint = ""
        # Tables that actually surfaced, read from chunk metadata, so we can attach
        # the right alias / unit caveats below.
        metas = results.get("metadatas") or []
        tables_in_context = [
            m.get("table_name") for m in (metas[0] if metas else []) if m
        ]

    # ── Alias / unit caveats for the tables in play (Phase 3 groundwork) ───
    context_notes = build_context_notes(tables_in_context)

    system_prompt = f"""You are an expert PostgreSQL engineer for an industrial machine vision company.
Your job is to convert the user's request into a flawless SQL query.

RULES:
1. Base your query ONLY on the provided SCHEMA CONTEXT.
2. Do not hallucinate column names.
3. Output ONLY the raw SQL code. Do not include markdown formatting, explanations, or pleasantries.
4. Always include model_name in the SELECT clause.
5. SELECT only the columns that are directly relevant to the user's question. Do not add extra columns.

SUPERLATIVE QUERIES:
When a user asks for a "maximum", "minimum", "fastest", "cheapest", or "costliest" lens, they want the specific lens model record, not an isolated aggregate number.
CRITICAL: Since columns like list_price, weight_g, etc., can contain NULL values, you MUST filter them out so NULLs are not sorted first.
Example: "What is the fastest lens?" -> SELECT model_name, f_no_min FROM [table] WHERE f_no_min IS NOT NULL ORDER BY f_no_min ASC LIMIT 1;
Example: "What is the cheapest lens?" -> SELECT model_name, list_price FROM [table] WHERE list_price IS NOT NULL ORDER BY list_price ASC LIMIT 1;
Example: "What is the costliest lens?" -> SELECT model_name, list_price FROM [table] WHERE list_price IS NOT NULL ORDER BY list_price DESC LIMIT 1;

ENGINEERING GLOSSARY (apply these mappings EXACTLY in every query):
- "Maximum Aperture", "Widest Aperture", or "Fastest Lens" ALWAYS maps to the `f_no_min` column (lower f-number = wider aperture).
- "Minimum Aperture" or "stopped down the most" ALWAYS maps to the `f_no_max` column (higher f-number = smaller aperture). Use ORDER BY f_no_max DESC LIMIT 1 to find the lens that stops down the most.
- "Warping" or "distortion" maps to `tv_distortion_percent`.
- "Edge brightness", "relative illuminance", or "uniformity" maps to `relative_illuminance_percent`. NOTE: Percentages are stored as whole numbers (e.g., 75% is 75). If a user queries > X%, you MUST include the exact value if the companion operator is '>' or '>='. For example, use: `(relative_illuminance_percent > X OR (relative_illuminance_percent = X AND relative_illuminance_operator IN ('>', '>=')))`.
- "Standoff" or "working distance" maps to `wd_mm`. NOTE: Some tables use `wd_min_mm` and `wd_max_mm` for a working distance range instead of a single `wd_mm`. Check the SCHEMA CONTEXT to determine which columns are available.
- "Total conjugate distance" maps to `o_i`.
- "Telecentricity" maps to `telecentricity_degrees`.
- "Depth of field" or "DOF" maps to `dof_mm`.
- "Numerical aperture" or "NA" maps to `numerical_aperture` (or `numerical_aperture_min`/`numerical_aperture_max` for ranges).
- "Sensor format" or "sensor size" maps to `sensor_size_raw`.
- "Megapixel" or "MP" maps to `megapixel_rating`.
- "MOD" or "minimum object distance" maps to `mod_distance_m` (in meters).
- "Zoom type" maps to `zoom_type` (manual / motorized).
- "Wavelength" maps to `wavelength_min_nm` / `wavelength_max_nm` or `wavelength_raw`.
- "Response time" maps to `response_time_ms`.
- "Adapter" or "mount conversion" — check `mount_primary_raw` and `mount_secondary_raw` in adapter/ring tables.

CROSS-TABLE QUERIES:
If the user asks a general question comparing across all lenses without specifying a specific product family, you MUST query across all relevant tables.
- Use `UNION ALL` to combine results from all tables in the SCHEMA CONTEXT that contain the requested columns.
- DO NOT just query a single table. Ensure you include EVERY relevant table from the context.
- CRITICAL SYNTAX RULE: Do NOT place semicolons (;) at the end of the individual SELECT statements within a UNION ALL. Only place a single semicolon at the very end of the final query.

{routing_hint}{context_notes}SCHEMA CONTEXT:
{chr(10).join(contexts)}"""

    # Lazy instantiate the validator to prevent disk I/O overhead on every loop iteration
    global _validator
    if '_validator' not in globals() or _validator is None:
        from sql_validator import SQLValidator
        _validator = SQLValidator()

    # --------------------------------------------------------------------------
    # SELF-HEALING RETRY LOOP
    # --------------------------------------------------------------------------
    # 1. We allow an initial generation attempt plus up to 2 retries (total 3 tries).
    # 2. On failure, we append the bad SQL and the validator's failure reason to the
    #    message history and ask the LLM to correct its mistake.
    # 3. If validation passes, we break the loop and return the SQL immediately.
    # 4. If we hit the retry limit and still fail, we return the last bad SQL so the
    #    main execution pipeline can log the failure appropriately.
    # --------------------------------------------------------------------------

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    max_retries = 2
    attempts = 0
    clean_sql = ""

    while attempts <= max_retries:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0, "num_ctx": 8192},
        )
        raw_response = response["message"]["content"]
        clean_sql = extract_sql_from_text(raw_response)

        # Validate the generated SQL
        val_result = _validator.validate(clean_sql)
        if val_result.is_valid:
            # SQL is structurally sound and schema-compliant
            break

        attempts += 1
        if attempts <= max_retries:
            # Self-Heal: Append the failure context as a new user message prompting correction
            correction_prompt = (
                f"The SQL you generated failed validation.\n"
                f"Bad SQL:\n{clean_sql}\n"
                f"Validation Error: {val_result.reason}\n"
                f"Please fix the error and output only the corrected raw SQL based strictly on the SCHEMA CONTEXT."
            )
            # Add the model's bad response and the user's correction instruction to the conversation
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": correction_prompt})
            print(f"  [Self-Healing] Attempt {attempts}/{max_retries}. Reason: {val_result.reason}")

    return clean_sql, contexts, filters
