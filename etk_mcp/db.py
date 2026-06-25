"""
etk_mcp/db.py
═════════════════════════════════════════════════════════════════════════════════
Decoupled read-only database access for the MCP server.

Owns its OWN psycopg2 connection to the Supabase Postgres pooler — it does NOT
import the agent's `pipeline` module (which would pull in ChromaDB + Ollama at
import time). Every query is read-only, statement-timeout bounded, row-capped, and
served through a small in-process TTL cache so repeated reads don't hit the DB.
═════════════════════════════════════════════════════════════════════════════════
"""
import datetime
import decimal
import os
import time

import psycopg2
from dotenv import load_dotenv

# Load .env from the repo root (one level up from this package).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "6543"),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "options": "-c search_path=ragav",
}

# Safety / performance limits
STATEMENT_TIMEOUT_MS = int(os.getenv("ETK_STATEMENT_TIMEOUT_MS", "15000"))
ROW_CAP = int(os.getenv("ETK_ROW_CAP", "1000"))
CACHE_TTL_S = int(os.getenv("ETK_CACHE_TTL_S", "300"))

_cache: dict = {}  # key -> (timestamp, payload)


def get_connection():
    """Open a fresh read-only psycopg2 connection scoped to the 'ragav' schema."""
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


def _jsonable(v):
    """Coerce DB values into JSON-serialisable Python types."""
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v


def safe_execute(sql: str, params: tuple = None, use_cache: bool = True) -> dict:
    """Run a read-only query and return a structured result.

    Returns {"columns": [...], "rows": [ {col: val} ], "row_count": N, "truncated": bool}.
    Raises on DB error (callers wrap into an {"error": ...} payload).
    """
    cache_key = (sql, params)
    now = time.time()
    if use_cache and cache_key in _cache:
        ts, payload = _cache[cache_key]
        if now - ts < CACHE_TTL_S:
            return payload

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS};")
        cur.execute(sql, params)
        columns = [d[0] for d in cur.description] if cur.description else []
        fetched = cur.fetchmany(ROW_CAP + 1) if columns else []
        truncated = len(fetched) > ROW_CAP
        rows = [
            {col: _jsonable(val) for col, val in zip(columns, r)}
            for r in fetched[:ROW_CAP]
        ]
        payload = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }
        if use_cache:
            _cache[cache_key] = (now, payload)
        return payload
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def clear_cache():
    """Drop the query cache (e.g. after a known data refresh)."""
    _cache.clear()
