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

# Request Models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    sql: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = None
    status: str

def create_empty_state(user_input: str = "") -> dict:
    return {
        "user_input": user_input,
        "filters": {},
        "products": [],
        "errors": [],
    }

def synthesize_response(user_query: str, status: str, count: int, products: list, sql: str, error_msg: str = "") -> str:
    """Uses Ollama to synthesize the database results into a conversational AI response."""
    
    if status == "error":
        system_prompt = "You are a helpful EarthTekniks AI Assistant. The user's query resulted in an error. Explain this to the user gracefully."
        user_message = f"User asked: {user_query}\nError encountered: {error_msg}\nWrite a brief, polite response."
    
    elif status == "no_results":
        system_prompt = "You are a helpful EarthTekniks AI Assistant. Explain to the user that no lenses were found matching their criteria."
        user_message = f"User asked: {user_query}\nStatus: No results found in the catalog.\nWrite a brief, polite response."
        
    else:
        system_prompt = """You are an expert EarthTekniks AI Assistant. Your goal is to synthesize the results of a database query into a neat, conversational, and professional response for the user.
Follow these rules:
1. Greet the user and directly answer their question.
2. If there are products, summarize the best matches or key specifications. Use a markdown list or table if appropriate.
3. Be concise but professional. Do not sound robotic.
4. Do NOT mention SQL, queries, or database tables. Speak as if you personally found the lenses.
5. CRITICAL: All list_price values in the database are in Indian Rupees (₹ / INR). You MUST format list prices correctly as Rupees (e.g., ₹109,035 or INR 109,035). Do NOT treat them as Yen. price_usd values are in US Dollars (e.g., $350 or USD 350).
"""
        # Truncate products to top 5 for the LLM prompt to avoid massive context
        top_products = products[:5]
        user_message = f"User asked: {user_query}\nWe found {count} total matching products.\nHere are the top matches: {json.dumps(top_products, indent=2)}\n\nSynthesize this into a polished response."

    try:
        response = ollama.chat(
            model="qwen2.5-coder",
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
        
        # 1. Execute SQL Agent
        state = create_empty_state(user_input=query)
        state = agent.execute(state)
        result = state.get("sql_agent_result", {})
        
        # Extract metadata
        sql = result.get("sql", "")
        status = result.get("status", "unknown")
        count = result.get("count", 0)
        products = result.get("products", [])
        
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
            error_msg=error_msg
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
