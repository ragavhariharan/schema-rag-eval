"""
scope.py
═════════════════════════════════════════════════════════════════════════════════
Scope gate for the SQL Agent.

Binary classifier: decides whether a query is answerable from the lens product
catalog (sql) or not (not_sql). Keeps the SQA from attempting SQL for chitchat,
engineering calculations, or company questions.

classify_scope(query) → {"scope": "sql" | "not_sql", "reason": <str>}

Bias: when uncertain, prefer "sql" — most traffic here is catalog lookups.
═════════════════════════════════════════════════════════════════════════════════
"""
import json

import ollama

from pipeline import OLLAMA_MODEL

SCOPE_LABELS = {"sql", "not_sql"}

_SYSTEM_PROMPT = """You classify queries for an industrial machine-vision LENS catalog assistant.
Decide: can this query be answered by looking up or filtering the lens product database?

Return ONLY JSON: {"scope": "<label>", "reason": "<short reason>"}

LABELS:
- "sql": The query can be answered by looking up or filtering lens products — by model
  name, specification (focal length, aperture, weight, price, FOV, etc.), family, or count.
- "not_sql": Anything else — engineering calculations from raw parameters, company/website
  questions (shipping, returns, contact), greetings, smalltalk, or unrelated topics.

KEY DISTINCTION:
- Asking for a stored attribute of a product → "sql"
- Plugging raw numbers into a formula to compute a value → "not_sql"
- Company/website/policy questions → "not_sql"
- Greetings or chitchat → "not_sql"

EXAMPLES:
- "MV11051B fov?" → {"scope":"sql","reason":"stored spec of a named model"}
- "cheapest telecentric lens" → {"scope":"sql","reason":"catalog filter"}
- "lenses under 200g" → {"scope":"sql","reason":"catalog filter by weight"}
- "calculate FOV for a 25mm lens at 500mm" → {"scope":"not_sql","reason":"formula computation"}
- "does EarthTekniks ship to India" → {"scope":"not_sql","reason":"company question"}
- "hello" → {"scope":"not_sql","reason":"greeting"}

When uncertain, choose "sql"."""


def classify_scope(query: str) -> dict:
    """Classify a query as 'sql' or 'not_sql'. Defaults to 'sql' on any error."""
    fallback = {"scope": "sql", "reason": "default (classifier unavailable)"}
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            format="json",
            options={"temperature": 0, "num_ctx": 4096},
        )
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError, Exception):
        return fallback

    scope = str(parsed.get("scope", "")).lower().strip()
    if scope not in SCOPE_LABELS:
        return fallback
    return {"scope": scope, "reason": str(parsed.get("reason", ""))[:200]}
