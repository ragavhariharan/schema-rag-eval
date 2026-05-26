import chromadb
import ollama

def generate_local_sql():
    # 1. Connect to our local ChromaDB instance
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="lens_schema_rag")

    # 2. Define the engineer's natural language request
    user_query = "wide aperture for low-light scanning with long standoff distance"

    # 3. Retrieve the context using hard metadata filters and vector similarity
    print("Retrieving context from ChromaDB...\n")
    results = collection.query(
        query_texts=[user_query],
        n_results=3, 
        where={
            "$and": [
                {"resolution_target": "16K"},
                {"pixel_pitch_um": 5.0}
            ]
        }
    )

    # 4. Extract the raw text payloads from the retrieved chunks
    retrieved_chunks = results['documents'][0]
    
    # Combine the chunks into a single formatted string for the LLM
    context_string = "\n\n".join(retrieved_chunks)

    # 5. Build the strict System Prompt
    # This instructs the model on exactly how to behave and provides the schema context
    system_prompt = f"""You are an expert PostgreSQL engineer for an industrial machine vision company.
Your job is to convert the user's request into a flawless SQL query.

RULES:
1. Base your query ONLY on the provided SCHEMA CONTEXT.
2. Do not hallucinate column names.
3. Output ONLY the raw SQL code. Do not include markdown formatting, explanations, or pleasantries.

SCHEMA CONTEXT:
{context_string}
"""

    # 6. Send the prompt and context to the local Ollama model
    print("Sending context to local qwen2.5-coder model for SQL generation...\n")
    response = ollama.chat(
        model='qwen2.5-coder', 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query}
        ]
    )

    # 7. Output the final generated SQL
    print("=== GENERATED SQL ===")
    print(response['message']['content'])
    print("=====================")

if __name__ == "__main__":
    generate_local_sql()