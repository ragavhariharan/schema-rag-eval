import chromadb
import json

def test_retrieval():
    # 1. Connect to our local database
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="lens_schema_rag")

    # 2. The Engineer's Query
    user_query = "wide aperture for low-light scanning with long standoff distance"

    # 3. The Orchestration (Hard Filters + Vector Search)
    print(f"\nSearching for: '{user_query}'")
    print("Applying hard filters: 16K resolution, 5.0µm pixel pitch...\n")
    
    results = collection.query(
        query_texts=[user_query],
        n_results=3, # Bring back the top 3 best chunks
        where={
            "$and": [
                {"resolution_target": "16K"},
                {"pixel_pitch_um": 5.0}
            ]
        }
    )

    # 4. Format and print the results beautifully
    if not results['documents'][0]:
        print("No results found. Check your filters.")
        return

    print("=== TOP RETRIEVAL HITS ===")
    for i in range(len(results['documents'][0])):
        score = results['distances'][0][i]
        chunk_id = results['ids'][0][i]
        text = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        
        print(f"\n--- Rank {i+1} (Distance: {score:.4f}) ---")
        print(f"ID: {chunk_id}")
        print(f"Type: {meta.get('chunk_type')} | Semantic Group: {meta.get('semantic_group', 'N/A')}")
        print(f"Aliases: {meta.get('aliases', [])}")
        print(f"Text Payload:\n{text}")
        print("-" * 50)

if __name__ == "__main__":
    test_retrieval()