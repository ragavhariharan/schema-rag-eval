import json
import chromadb

def ingest_to_chroma():
    # 1. Initialize a persistent local ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # 2. Delete existing collection to ensure a clean slate, then create new
    try:
        client.delete_collection(name="lens_schema_rag")
    except Exception:
        # Collection might not exist yet. Older ChromaDB raised ValueError here;
        # newer versions raise chromadb.errors.NotFoundError — catch both.
        pass
    collection = client.create_collection(name="lens_schema_rag")
    
    # 3. Load our enriched semantic chunks
    with open("chroma_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    ids = []
    texts = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        texts.append(chunk["text"])
        
        # ----------------------------------------------------
        # SANITIZATION STEP: Clean metadata for ChromaDB
        # ----------------------------------------------------
        clean_meta = {}
        for key, value in chunk["metadata"].items():
            # Skip null/None values
            if value is None:
                continue
            # Skip empty lists
            if isinstance(value, list) and len(value) == 0:
                continue
                
            clean_meta[key] = value
            
        metadatas.append(clean_meta)
        
    # 4. Upsert the data into the database
    print(f"Embedding and ingesting {len(chunks)} chunks into ChromaDB...")
    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )
    
    print("Ingestion complete! Database is ready for queries.")

if __name__ == "__main__":
    ingest_to_chroma()