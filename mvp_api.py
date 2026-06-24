import json
import logging
import ollama
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sql_agent import SQLAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="SQL Agent MVP API")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the SQL Agent once
agent = SQLAgent()

# Deterministic handoff replies when the query isn't the catalog agent's job.
# (In the full assistant the orchestrator would route to the named agent;
# standalone, the SQA explains and defers.)
OUT_OF_SCOPE_MESSAGES = {
    "calculation": (
        "That looks like an engineering calculation. I'm the EarthTekniks product-"
        "catalog assistant — our calculation assistant can compute that (FOV, "
        "magnification, depth of field, sensor maths, etc.). I can, however, look up "
        "the specs of any lens in our catalog."
    ),
    "domain": (
        "That's a question about EarthTekniks itself. Our website/company assistant "
        "can help with that. I'm here for lens-catalog lookups — models, specs, and "
        "prices."
    ),
    "chitchat": (
        "Hi! I'm the EarthTekniks lens-catalog assistant. Ask me about a lens model, "
        "a specification (FOV, focal length, aperture, working distance…), or to find "
        "lenses by price or family."
    ),
    "default": (
        "I'm the EarthTekniks lens-catalog assistant — I can look up lens models, "
        "specifications, and prices. Could you rephrase your question around the lens "
        "catalog?"
    ),
}

# Request Models
class ChatRequest(BaseModel):
    query: str
    # Prior turns ([{role: "user"|"assistant", content: str}, ...]) for follow-ups
    # and clarification answers. The server is stateless — the client sends history.
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    sql: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = None
    status: str

def create_empty_state(user_input: str = "", history: list = None) -> dict:
    return {
        "user_input": user_input,
        "history": history or [],
        "filters": {},
        "products": [],
        "errors": [],
    }

def synthesize_response(user_query: str, status: str, count: int, products: list, sql: str, error_msg: str = "", assumption: str = "") -> str:
    """Uses Ollama to synthesize the database results into a conversational AI response."""

    if status == "error":
        system_prompt = "You are a helpful EarthTekniks AI Assistant. The user's query resulted in an error. Explain this to the user gracefully."
        user_message = f"User asked: {user_query}\nError encountered: {error_msg}\nWrite a brief, polite response."

    elif status == "no_results":
        system_prompt = (
            "You are a helpful EarthTekniks lens-catalog assistant. No products matched the user's "
            "criteria. Explain that briefly and helpfully, and suggest how they might broaden or adjust "
            "the search (e.g. relax a spec or try a related lens family). Keep it short."
        )
        assume_line = f"\nNote: you interpreted the request as: {assumption}" if assumption else ""
        user_message = f"User asked: {user_query}{assume_line}\nStatus: no matching lenses found.\nWrite a brief, helpful response."

    else:
        system_prompt = """You are an expert EarthTekniks lens-catalog assistant. Turn the retrieved product data into a clear, helpful, well-explained answer.
Rules:
1. Directly answer the user's question first.
2. If you were given an ASSUMPTION, open by briefly stating it (e.g. "Assuming you mean … —") so the user knows how you interpreted their request.
3. Present the matches cleanly: a markdown table for several products, or a short labelled list for one or two. Include the specifications relevant to the question.
4. Add ONE short line of helpful context where useful (why this answers their question, or a notable trade-off). Don't pad.
5. Be conversational and professional, not robotic. Do NOT mention SQL, queries, databases, or tables-as-in-database.
6. CRITICAL: list_price values are in Indian Rupees (₹ / INR) — format as e.g. ₹109,035. price_usd values are US Dollars (e.g. $350). Never treat prices as Yen.
"""
        top_products = products[:8]
        assume_line = f"\nAssumption you made (state it briefly): {assumption}" if assumption else ""
        user_message = (
            f"User asked: {user_query}{assume_line}\n"
            f"Found {count} matching product(s). Data for the top matches:\n{json.dumps(top_products, indent=2)}\n\n"
            f"Write the answer following the rules."
        )

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama synthesis failed: {e}")
        return "I found some results, but I encountered an issue synthesizing my response. Please check the raw data."

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        logger.info(f"Processing query: {query}")
        
        # 1. Execute SQL Agent (history enables follow-ups + clarification answers)
        state = create_empty_state(user_input=query, history=request.history)
        state = agent.execute(state)
        result = state.get("sql_agent_result", {})

        # Extract metadata
        sql = result.get("sql", "")
        status = result.get("status", "unknown")
        count = result.get("count", 0)
        products = result.get("products", [])
        assumption = result.get("assumption", "")

        # ── Phase 3: out-of-scope handoff ─────────────────────────────────
        # Query belongs to the calculation or domain agent (or is chitchat).
        # Reply with a clean, deterministic handoff — no SQL, no LLM synthesis.
        if status == "out_of_scope":
            return ChatResponse(
                response=OUT_OF_SCOPE_MESSAGES.get(
                    result.get("scope"), OUT_OF_SCOPE_MESSAGES["default"]
                ),
                sql=None,
                products=None,
                status=status,
            )

        # ── Phase 5: clarification — ask the question, run no SQL ──────────
        if status == "needs_clarification":
            return ChatResponse(
                response=result.get("message", "Could you give a bit more detail?"),
                sql=None,
                products=None,
                status=status,
            )

        error_msg = ""
        if status == "error":
            error_msg = result.get("message", "Unknown error")

        # 2. Synthesize AI Response
        ai_response_text = synthesize_response(
            user_query=query,
            status=status,
            count=count,
            products=products,
            sql=sql,
            error_msg=error_msg,
            assumption=assumption,
        )
        
        return ChatResponse(
            response=ai_response_text,
            sql=sql if sql else None,
            products=products if status == "success" else None,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Start the server
    logger.info("Starting MVP FastAPI server on port 8000")
    uvicorn.run("mvp_api:app", host="0.0.0.0", port=8000, reload=True)
