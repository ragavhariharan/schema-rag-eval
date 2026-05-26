# schema-rag-eval

Repository for schema RAG evaluation and ingestion scripts.

Contents:
- `generate_chunks.py` — generate semantic chunks
- `ingest_chroma.py` — ingest chunks into ChromaDB
- `chroma_chunks.json` — example chunks

Setup:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run ingestion:
```
python ingest_chroma.py
```
