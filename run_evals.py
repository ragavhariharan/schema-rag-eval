import json
import chromadb
import ollama
import sqlite3
import pandas as pd

# Initialize the vector database connection for retrieval
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="lens_schema_rag")

def extract_filters(user_query: str) -> dict:
    extraction_prompt = f"""You are a data extractor. 
Analyze the user's query and extract the camera resolution and pixel pitch if mentioned.
Return ONLY a valid JSON object. Do not include markdown formatting or explanations.
If a value is not mentioned, set it to null.
Example Query: "I need a fast 16K lens with 5 micron pitch."
Example Output: {{"resolution_target": "16K", "pixel_pitch_um": 5.0}}
Note: "u" is shorthand for microns (e.g., "5u" = 5.0).
User Query: "{user_query}"
Output:"""

    response = ollama.chat(model='qwen2.5-coder', messages=[{'role': 'user', 'content': extraction_prompt}])
    try:
        return json.loads(response['message']['content'])
    except:
        return {"resolution_target": None, "pixel_pitch_um": None}

def run_pipeline(user_query: str) -> str:
    filters = extract_filters(user_query)
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

    search_params = {"query_texts": [user_query], "n_results": 5}
    if where_clause:
        search_params["where"] = where_clause
        
    results = collection.query(**search_params)

    if not results['documents'] or not results['documents'][0]:
        return "ERROR: No context retrieved."

    context_string = "\n\n".join(results['documents'][0])
    system_prompt = f"""You are an expert PostgreSQL engineer for an industrial machine vision company.
Your job is to convert the user's request into a flawless SQL query.
RULES:
1. Base your query ONLY on the provided SCHEMA CONTEXT.
2. Do not hallucinate column names.
3. Output ONLY the raw SQL code without markdown formatting or explanations.
ENGINEERING GLOSSARY:
- "Maximum Aperture", "Widest Aperture", or "Fastest Lens" ALWAYS refers to the `f_no_min` column.
- "Minimum Aperture" ALWAYS refers to the `f_no_max` column.
SCHEMA CONTEXT:
{context_string}
"""
    
    response = ollama.chat(model='qwen2.5-coder', messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_query}])
    return response['message']['content'].replace("```sql", "").replace("```", "").strip()

def execute_and_compare(generated_sql: str, expected_sql: str) -> bool:
    """
    Connects to the local test database, executes both queries, 
    and compares the resulting dataframes. 
    """
    conn = sqlite3.connect('test_catalog.db')
    
    try:
        # Fetch data for both queries
        df_expected = pd.read_sql_query(expected_sql, conn)
        df_generated = pd.read_sql_query(generated_sql, conn)
        
        # If the dataframes are identical (same data, same rows), it's a pass!
        if df_expected.equals(df_generated):
            return True
        else:
            return False
    except Exception as e:
        # If the generated SQL has a syntax error or hallucinates a column, it crashes here and fails.
        return False
    finally:
        conn.close()

def run_evaluations():
    with open("golden_dataset.json", "r") as f:
        dataset = json.load(f)

    # For this test, let's just run the first 3 queries that correspond to our dummy database
    subset = dataset[:3]
    total_tests = len(subset)
    passed_tests = 0

    print("="*50)
    print(f"🚀 STARTING EXECUTION EVALUATION: {total_tests} Tests")
    print("="*50)

    for test in subset:
        print(f"\nEvaluating: [{test['id']}]")
        generated_sql = run_pipeline(test['question'])
        
        # The ultimate test: Do they return the same data?
        is_pass = execute_and_compare(generated_sql, test['expected_sql'])
        
        if is_pass:
            passed_tests += 1
            print("✅ Status: PASS (Data Matches Exactly)")
        else:
            print("❌ Status: FAIL (Data Mismatch or Syntax Error)")
            print(f"Expected: {test['expected_sql']}")
            print(f"Generated: {generated_sql}")

    accuracy = (passed_tests / total_tests) * 100
    print("\n" + "="*50)
    print(f"📊 EVALUATION COMPLETE")
    print(f"True Execution Accuracy: {accuracy:.1f}% ({passed_tests}/{total_tests})")
    print("="*50)

if __name__ == "__main__":
    run_evaluations()