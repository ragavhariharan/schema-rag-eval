"""
conversation.py
═════════════════════════════════════════════════════════════════════════════════
Conversational understanding layer (Phase 5).

Runs AFTER the scope gate (so we know it's a catalog query) and BEFORE SQL
generation. Given the new message plus the conversation history, it:

  1. Rewrites the message into a SELF-CONTAINED query, resolving follow-ups
     ("its weight", "the cheaper one", "show telecentric instead") against
     earlier turns.
  2. Decides whether the request is ANSWERABLE or too vague — in which case it
     returns ONE clarifying question instead of guessing.
  3. Captures an ASSUMPTION when it had to interpret a vague term, so the final
     answer can state it ("best for low light" → widest aperture).

Principle: prefer a stated assumption over a question. Only ask when proceeding
would be blind guessing (no lens, family, or spec to act on).

assess_query(query, history) → {
    "standalone_query": str,            # self-contained query for the pipeline
    "answerable": bool,
    "clarifying_question": str | None,  # set when answerable is False
    "assumption": str | None,           # set when a vague term was interpreted
}
═════════════════════════════════════════════════════════════════════════════════
"""
import json

import ollama

from pipeline import OLLAMA_MODEL

# Keep the prompt small: only the most recent turns matter for resolving refs.
MAX_HISTORY_MESSAGES = 6

_SYSTEM_PROMPT = """You are the query-understanding step of an industrial machine-vision LENS catalog assistant.
The catalog stores lens PRODUCTS and their specs — model name, focal length, price, F-number/aperture,
field of view, working distance, magnification, sensor size, weight, mount, depth of field, telecentricity,
wavelength, etc. — across families (FA, telecentric, line scan, macro, zoom, microscope, spectral, M12,
autofocus, large format, 3-CMOS, anti-vibration, inspection, accessories).

Given the conversation so far and the user's NEW message, return ONLY this JSON:
{
  "standalone_query": "<the request rewritten as a self-contained catalog question, resolving references to earlier turns>",
  "answerable": true or false,
  "clarifying_question": "<if NOT answerable, ONE short question>" or null,
  "assumption": "<if you interpreted a vague term to make it answerable, a short note>" or null
}

RULES:
- PREFER answering with a sensible assumption over asking. Set answerable=false ONLY when the request is
  too vague to pick even a lens family or a spec (e.g. "fov?" with no lens named, "I need a lens" with no
  requirement, "tell me about lenses").
- When you assume, keep it reasonable and record it briefly:
    "best" / "good" → lowest price (best value);  "good for low light" / "fast" → widest aperture (lowest F-number);
    "small" / "compact" → smallest size or weight;  "high resolution" → highest megapixel.
- Resolve follow-ups using the history. "its <spec>" / "that lens" → the specific model from the previous answer.
  "the cheaper/lighter one" → the matching item discussed. "what about <spec>" → same subject, new spec.
- standalone_query must be answerable by a catalog lookup. Do not invent model names or specs.

EXAMPLES (new message → JSON):
- "cheapest telecentric lens" -> {"standalone_query":"cheapest telecentric lens","answerable":true,"clarifying_question":null,"assumption":null}
- "fov?" (no prior context) -> {"standalone_query":"field of view","answerable":false,"clarifying_question":"Which lens model or lens family would you like the field of view for?","assumption":null}
- "I need a lens" -> {"standalone_query":"lens recommendation","answerable":false,"clarifying_question":"What's the application or key requirement — lens family, focal length, working distance, sensor size, or budget?","assumption":null}
- "best lens for low light" -> {"standalone_query":"lens with the widest aperture (lowest F-number)","answerable":true,"clarifying_question":null,"assumption":"Interpreting 'best for low light' as the widest aperture (lowest F-number)."}
- history: user "cheapest telecentric lens"; assistant "The cheapest is TC0501A at ...". new "what about its weight?" -> {"standalone_query":"weight of telecentric lens TC0501A","answerable":true,"clarifying_question":null,"assumption":null}"""


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


def assess_query(query: str, history=None) -> dict:
    """Understand the query in context. Fails safe to 'answerable as-is' so a
    classifier hiccup never blocks a legitimate lookup."""
    fallback = {
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

    answerable = bool(parsed.get("answerable", True))
    standalone = parsed.get("standalone_query") or query
    clarifying = parsed.get("clarifying_question")
    assumption = parsed.get("assumption")

    # If the model says "not answerable" but gave no question, fail open.
    if not answerable and not clarifying:
        return fallback

    return {
        "standalone_query": str(standalone),
        "answerable": answerable,
        "clarifying_question": str(clarifying) if clarifying else None,
        "assumption": str(assumption) if assumption else None,
    }
