"""
scope.py
═════════════════════════════════════════════════════════════════════════════════
Scope gate for the SQL Agent (Phase 3).

The SQA is ONE of three agents in the EarthTekniks assistant (alongside a
calculation agent and a domain/website agent). On its own it would try to write
SQL for ANY input — including engineering-calculation questions, company/website
questions, and chitchat — and produce garbage. This classifier lets the SQA
recognise out-of-scope queries and decline cleanly, signalling which agent should
handle them instead.

classify_scope(query) → {"scope": <label>, "reason": <str>}

Labels:
  sql          — answerable from the lens product catalog (look up / filter /
                 compare products by their stored specs, price, or model name)
  calculation  — asks to COMPUTE an engineering value via a formula (FOV from
                 focal length + distance, magnification, DOF, sensor maths …)
  domain       — about EarthTekniks the company / website (shipping, contact,
                 ordering, warranty, "about us")
  chitchat     — greetings, thanks, smalltalk, or otherwise unrelated

Bias: when uncertain, prefer "sql" — the SQA is the catalog agent and most traffic
here is catalog lookups, so we'd rather attempt a lookup than wrongly reject one.
═════════════════════════════════════════════════════════════════════════════════
"""
import json

import ollama

# Reuse the lightweight router/filter model (not the heavier SQL model).
from pipeline import OLLAMA_MODEL

SCOPE_LABELS = {"sql", "calculation", "domain", "chitchat"}

# scope → which agent should handle it (None = handle conversationally here)
ROUTE_TO = {
    "calculation": "calculation_agent",
    "domain": "domain_agent",
    "chitchat": None,
    "sql": None,
}

_SYSTEM_PROMPT = """You classify a user's query for an industrial machine-vision LENS company assistant.
The assistant has three specialists. Decide which ONE should handle the query.

Return ONLY JSON: {"scope": "<label>", "reason": "<short reason>"}

LABELS:
- "sql": The query can be answered by LOOKING UP or FILTERING lens products in the
  product catalog/database — by model name, specification, price, or family.
  Examples: stored specs of a named model, "cheapest X lens", "lenses with Y",
  comparing catalog products, counts of products.
- "calculation": The query asks to COMPUTE or DERIVE an engineering value from
  given parameters using a formula (not look up a stored value).
  Examples: field of view from focal length and working distance, required
  magnification for an object size and sensor, depth of field, sensor maths.
- "domain": The query is about EarthTekniks the COMPANY or WEBSITE — shipping,
  contact, ordering, lead time, warranty, returns, "about us", support.
- "chitchat": Greetings, thanks, smalltalk, or anything unrelated to lenses.

KEY DISTINCTION (sql vs calculation):
- If the query names a model or asks for a product's stored attribute, or filters
  the catalog → "sql".
- If the query gives raw numbers to plug into a formula and wants a COMPUTED answer
  → "calculation".

EXAMPLES:
- "MV11051B fov?" -> {"scope":"sql","reason":"stored FOV spec of a named model"}
- "cheapest telecentric lens" -> {"scope":"sql","reason":"catalog filter + superlative"}
- "which lenses are under 200 grams" -> {"scope":"sql","reason":"catalog filter"}
- "calculate the field of view for a 25mm lens at 500mm working distance" -> {"scope":"calculation","reason":"compute FOV from parameters"}
- "what magnification do I need to image a 10mm object on a 1 inch sensor" -> {"scope":"calculation","reason":"derive magnification"}
- "does EarthTekniks ship to India" -> {"scope":"domain","reason":"company shipping question"}
- "what is your return policy" -> {"scope":"domain","reason":"company policy"}
- "hello there" -> {"scope":"chitchat","reason":"greeting"}

When uncertain, choose "sql"."""


def classify_scope(query: str) -> dict:
    """Classify a query into one of SCOPE_LABELS. Defaults to 'sql' on any
    parsing/label error (fail safe toward attempting a catalog lookup)."""
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
