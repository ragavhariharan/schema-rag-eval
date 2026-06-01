import json
import chromadb
import ollama

# 1. Initialize Database
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="lens_schema_rag")

def extract_filters(user_query: str) -> dict:
    """Uses the LLM to extract hard metadata filters dynamically."""
    extraction_prompt = f"""You are a data extractor. 
Analyze the user's query and extract the camera resolution and pixel pitch if mentioned.
Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
If a value is not mentioned, set it to null.

Example Query: "I need a fast 16K lens with 5 micron pitch."
Example Output: {{"resolution_target": "16K", "pixel_pitch_um": 5.0}}
Note: "u" is shorthand for microns (e.g., "5u" = 5.0).
User Query: "{user_query}"
Output:"""

    response = ollama.chat(
        model='qwen2.5-coder', 
        messages=[{'role': 'user', 'content': extraction_prompt}]
    )
    
    try:
        return json.loads(response['message']['content'])
    except json.JSONDecodeError:
        return {"resolution_target": None, "pixel_pitch_um": None}

def stress_test_loop():
    print("\n" + "="*50)
    print("🔍 RAG STRESS TEST TERMINAL")
    print("Type 'exit' or 'quit' to stop.")
    print("="*50)

    while True:
        user_query = input("\n👤 You: ")
        if user_query.lower() in ['exit', 'quit']:
            print("Exiting stress test...")
            break
        if not user_query.strip():
            continue

        print("\n⚙️  Processing...")

        # 1. Extract Filters Dynamically
        filters = extract_filters(user_query)
        print(f"   [Filters Extracted]: {filters}")

        # 2. Build Where Clause
        where_clause = {}
        and_conditions = []
        if filters.get("resolution_target"):
            and_conditions.append({"resolution_target": filters["resolution_target"]})
        if filters.get("pixel_pitch_um"):
            and_conditions.append({"pixel_pitch_um": filters["pixel_pitch_um"]})

        if len(and_conditions) == 1:
            where_clause = and_conditions[0]
        elif len(and_conditions) > 1:
            where_clause = {"$and": and_conditions}

        # 3. Retrieve Context
        # 3. Retrieve Context
        search_params = {"query_texts": [user_query], "n_results": 5} # Changed from 3 to 5
        if where_clause:
            search_params["where"] = where_clause
            
        results = collection.query(**search_params)

        if not results['documents'] or not results['documents'][0]:
            print("   [!] No relevant schema chunks found.")
            continue

        # 4. Generate SQL
        context_string = "\n\n".join(results['documents'][0])
        system_prompt = f"""You are an expert PostgreSQL engineer for an industrial machine vision company.
Your job is to convert the user's request into a flawless SQL query.

RULES:
1. Base your query ONLY on the provided SCHEMA CONTEXT.
2. Do not hallucinate column names.
3. Output ONLY the raw SQL code without markdown formatting or explanations.

ENGINEERING GLOSSARY:
- "Maximum Aperture", "Widest Aperture", or "Fastest Lens" ALWAYS refers to the `f_no_min` column (a lower F-number means a wider physical aperture).
- "Minimum Aperture" ALWAYS refers to the `f_no_max` column.

SCHEMA CONTEXT:
{context_string}
"""
        response = ollama.chat(
            model='qwen2.5-coder', 
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_query}
            ]
        )

        # 5. Print Result
        print("\n🤖 Generated SQL:")
        print("-" * 40)
        print(response['message']['content'].strip())
        print("-" * 40)

if __name__ == "__main__":
    stress_test_loop()