# EarthTekniks SQL Agent (SQA)

Natural-language → SQL agent over the EarthTekniks machine-vision **lens catalog**.
It is the data-retrieval agent of a larger EarthTekniks AI assistant (the other
agents — a *calculation* agent and a *domain/website* agent — are built separately).

A user asks something like *"cheapest telecentric lens"* or *"MV11051B fov?"*, and
the SQA retrieves the answer from a Supabase PostgreSQL database of ~38 lens tables
(one per product family), then synthesizes a conversational reply.

> Source of truth for the data is `price_list_usd.xlsx`; its important sheets are
> normalized into Supabase tables (schema `ragav`), all keyed on `model_name`.

---

## How it works

```
frontend (mvp_frontend/) ──► mvp_api.py  /api/chat
                                 │
                                 ▼
                           sql_agent.py  SQLAgent.execute(state)
                                 │
                                 ▼
                           pipeline.run_pipeline(query)         ◄── core RAG pipeline
                             1. llm_extract_filters   (Ollama → product_type, …)
                             2. ChromaDB retrieval    (schema-doc chunks)
                             3. SQL generation        (Ollama + engineering glossary)
                             4. SQLValidator          (sqlglot: read-only + grounding)
                             5. self-healing loop     (≤2 retries on validator error)
                                 │
                                 ▼
                           execute_sql_safely(sql)  ──► Supabase (read-only)
                                 │
                                 ▼
                           synthesize_response()  (Ollama → prose for the user)
```

All models run **locally via [Ollama](https://ollama.com/)** (default
`llama3.1:8b`). Nothing is sent to a cloud LLM.

---

## Repository layout

### Runtime (production path)
| File | Role |
|------|------|
| `pipeline.py` | **Core RAG pipeline** — DB connection, ChromaDB retrieval, filter extraction, SQL generation + self-healing. Single source of truth, imported everywhere. |
| `sql_agent.py` | `SQLAgent` — state-in/state-out wrapper around the pipeline (the agent's public interface). |
| `sql_validator.py` | `SQLValidator` — sqlglot AST checks: read-only enforcement + table/column grounding against `schema_registry.json`. |
| `mvp_api.py` | FastAPI server exposing `POST /api/chat`; runs the agent and synthesizes a reply. |
| `mvp_frontend/` | Minimal HTML/CSS/JS chat UI. |

### Knowledge base (offline build)
| File | Role |
|------|------|
| `docs/*.md` | Per-table schema documentation (purpose, every column, example NL→SQL). The human-authored knowledge. |
| `generate_chunks.py` | Splits `docs/*.md` into one schema chunk per table → `chroma_chunks.json`. |
| `chroma_chunks.json` | Generated chunks (committed). |
| `ingest_chroma.py` | Loads `chroma_chunks.json` into a local ChromaDB (`chroma_db/`, gitignored). |
| `schema_registry.json` | Table → allowed-columns map used by the validator. |

### Evaluation & debugging
| File | Role |
|------|------|
| `run_execution_accuracy.py` | Execution-accuracy eval: compares generated vs. golden SQL by **result set** (`golden_dataset.json`). |
| `run_full_evaluation.py` | Broader harness: generation/safety metrics + AST diagnostics + pattern accuracy (`evaluation_dataset.json`). |
| `run_safety_benchmark.py` | Prompt-injection / hallucination traps (`safety_benchmark.json`). Needs `colorama`. |
| `run_sql_agent_debug.py` | Interactive 5-stage trace terminal for one query at a time. |

---

## Setup

Requires Python 3.10+, a running [Ollama](https://ollama.com/) instance, and access
to the Supabase database.

```bash
python -m venv venv
source venv/bin/activate
pip install chromadb ollama pandas psycopg2-binary python-dotenv sqlglot pydantic \
            fastapi uvicorn colorama

ollama pull llama3.1:8b
```

Create a `.env` (gitignored) with the database credentials:

```
DB_HOST=...
DB_PORT=6543
DB_NAME=postgres
DB_USER=...
DB_PASSWORD=...
```

Build the local schema index (run once, and after any change to `docs/`):

```bash
python generate_chunks.py     # docs/*.md  → chroma_chunks.json
python ingest_chroma.py       # chroma_chunks.json → chroma_db/
```

> `chroma_db/` is **per-folder** and gitignored. Run `ingest_chroma.py` and the app
> from the **same** directory so the app reads the chunks you just built.

---

## Running

```bash
# API server (frontend talks to this)
python mvp_api.py                  # http://localhost:8000  (POST /api/chat)

# Debug a single query end-to-end with full pipeline trace
python run_sql_agent_debug.py

# Evaluations
python run_execution_accuracy.py   # result-set accuracy vs golden_dataset.json
python run_full_evaluation.py      # full metrics suite
python run_safety_benchmark.py     # safety / injection traps
```

---

## Notes on the data

- `model_name` is the primary key in every table; there are no cross-table foreign keys.
- **Currency:** `list_price` is the **retail price in INR (₹)** — in `price_list_usd.xlsx`
  it is computed as `base USD × markup × the USD→INR dollar rate`. The separate
  `price_usd` column (where present) is the **base price in USD**. The two are not equal.
- Many specs are stored as both a raw text column (`*_raw`, query with `ILIKE`) and a
  parsed numeric column. FOV, F-number, and working distance use different column
  shapes across tables — always check the schema doc for the specific table.

See `SMART_SQA_PLAN.md` for the roadmap to make the agent handle any query phrasing
(including bare model-name lookups), not just queries that name the lens family.
