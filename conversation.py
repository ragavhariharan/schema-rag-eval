"""
conversation.py
═════════════════════════════════════════════════════════════════════════════════
Front-end UNDERSTANDING step (Phases 3 + 5, merged).

A single local-LLM call that does both jobs that used to be two separate calls
(scope classification + conversational understanding), halving the pre-pipeline
latency. Given the new message plus conversation history it decides:

  • scope        — which specialist should handle it: sql / calculation / domain / chitchat
  • standalone_query — the message rewritten self-contained (follow-ups resolved)
  • answerable   — for sql queries, whether it's specific enough to act on
  • clarifying_question — one question to ask when it's too vague
  • assumption   — a note when a vague term had to be interpreted

`understand(query, history)` is the production entry point. `scope.classify_scope`
is a thin wrapper over it (kept so the scope eval keeps working).

Principle: prefer a stated assumption over a question. When unsure about scope,
choose "sql" (the catalog agent is the default).
═════════════════════════════════════════════════════════════════════════════════
"""
import json

import ollama

from pipeline import OLLAMA_MODEL

SCOPE_LABELS = {"sql", "calculation", "domain", "chitchat"}

# Keep the prompt small: only the most recent turns matter for resolving refs.
MAX_HISTORY_MESSAGES = 6

_SYSTEM_PROMPT = """You are the front-end understanding step of an industrial machine-vision LENS catalog assistant.
The assistant has three specialists. The catalog stores lens PRODUCTS and their specs — model name, focal
length, price, F-number/aperture, field of view, working distance, magnification, sensor size, weight, mount,
depth of field, telecentricity, wavelength, megapixel — across families (FA, telecentric, line scan, macro,
zoom, microscope, spectral, M12, autofocus, large format, 3-CMOS, anti-vibration, inspection, accessories).

Given the conversation history and the user's NEW message, return ONLY this JSON:
{
  "scope": "sql" | "calculation" | "domain" | "chitchat",
  "standalone_query": "<the request rewritten as a self-contained catalog question, resolving references to earlier turns>",
  "answerable": true or false,
  "clarifying_question": "<if NOT answerable, ONE short question>" or null,
  "assumption": "<if you interpreted a vague term to make it answerable, a short note>" or null
}

SCOPE — which specialist:
- "sql": answerable by LOOKING UP or FILTERING lens products in the catalog (by model, spec, price, family).
- "calculation": COMPUTE/derive an engineering value from given parameters via a formula (field of view from
  focal length + working distance, required magnification, depth of field, sensor maths).
- "domain": about EarthTekniks the COMPANY or WEBSITE (shipping, contact, ordering, lead time, warranty, returns).
- "chitchat": greetings, thanks, smalltalk, or anything unrelated to lenses.
Distinguish sql vs calculation: naming a model, asking a product's stored attribute, or filtering the catalog
→ "sql"; giving raw numbers to plug into a formula and wanting a COMPUTED answer → "calculation".

UNDERSTANDING — only matters when scope = "sql". For calculation/domain/chitchat, set answerable=true,
clarifying_question=null, assumption=null, and standalone_query = the user's message unchanged.
- standalone_query: resolve follow-ups using history. "its <spec>" / "that lens" → the specific model from the
  previous answer. "the cheaper/lighter one" → the matching item. "what about <spec>" → same subject, new spec.
- answerable=false ONLY when the request is too vague to pick even a lens family or spec (e.g. "fov?" with no
  lens named, "I need a lens" with no requirement). Then give ONE clarifying_question. PREFER answering with an
  assumption over asking.
- assumption: when you interpret a vague term, record it briefly. "best"/"good" → lowest price (best value);
  "good for low light"/"fast" → widest aperture (lowest F-number); "small"/"compact" → smallest size or weight;
  "high resolution" → highest megapixel.

When uncertain about scope, choose "sql".

EXAMPLES (new message → JSON):
- "cheapest telecentric lens" -> {"scope":"sql","standalone_query":"cheapest telecentric lens","answerable":true,"clarifying_question":null,"assumption":null}
- "fov?" (no prior context) -> {"scope":"sql","standalone_query":"field of view","answerable":false,"clarifying_question":"Which lens model or lens family would you like the field of view for?","assumption":null}
- "best lens for low light" -> {"scope":"sql","standalone_query":"lens with the widest aperture (lowest F-number)","answerable":true,"clarifying_question":null,"assumption":"Interpreting 'best for low light' as the widest aperture (lowest F-number)."}
- history: user "cheapest telecentric lens"; assistant "The cheapest is TC0501A...". new "what about its weight?" -> {"scope":"sql","standalone_query":"weight of telecentric lens TC0501A","answerable":true,"clarifying_question":null,"assumption":null}
- "calculate the field of view for a 25mm lens at 500mm working distance" -> {"scope":"calculation","standalone_query":"calculate the field of view for a 25mm lens at 500mm working distance","answerable":true,"clarifying_question":null,"assumption":null}
- "does EarthTekniks ship to India?" -> {"scope":"domain","standalone_query":"does EarthTekniks ship to India?","answerable":true,"clarifying_question":null,"assumption":null}
- "hello there" -> {"scope":"chitchat","standalone_query":"hello there","answerable":true,"clarifying_question":null,"assumption":null}"""


def _format_history(history) -> list:
    """Trim and normalize history into chat messages for the model."""
    if not history:
        return []
    msgs = []
    for h in history[-MAX_HISTORY_MESSAGES:]:
        role = h.get("role")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": str(content)[:1500]})
    return msgs


def understand(query: str, history=None) -> dict:
    """Single-call scope + understanding. Fails safe to an answerable sql query
    so a classifier hiccup never blocks a legitimate lookup."""
    fallback = {
        "scope": "sql",
        "standalone_query": query,
        "answerable": True,
        "clarifying_question": None,
        "assumption": None,
    }

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(_format_history(history))
    messages.append({"role": "user", "content": query})

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format="json",
            options={"temperature": 0, "num_ctx": 8192},
        )
        parsed = json.loads(response["message"]["content"])
    except (json.JSONDecodeError, KeyError, Exception):
        return fallback

    scope = str(parsed.get("scope", "")).lower().strip()
    if scope not in SCOPE_LABELS:
        scope = "sql"

    answerable = bool(parsed.get("answerable", True))
    standalone = parsed.get("standalone_query") or query
    clarifying = parsed.get("clarifying_question")
    assumption = parsed.get("assumption")

    # Non-sql scopes are always "answerable" (handed off, not clarified here).
    if scope != "sql":
        answerable, clarifying, assumption = True, None, None

    # If sql but flagged unanswerable with no question, fail open.
    if scope == "sql" and not answerable and not clarifying:
        return fallback

    return {
        "scope": scope,
        "standalone_query": str(standalone),
        "answerable": answerable,
        "clarifying_question": str(clarifying) if clarifying else None,
        "assumption": str(assumption) if assumption else None,
    }
