# Smart SQL Agent (SQA) — Evolution Plan

> Goal: evolve the EarthTekniks SQL Agent from a template matcher (only handles
> queries where the lens family is stated, e.g. *"cheapest telecentric lens"*)
> into an agent that answers **any** catalog query however it is worded —
> including bare model-name lookups like *"MV11051B fov?"* — using a **fully
> local (Ollama) model stack**.
>
> Decision locked: **stay fully local.** No Claude/cloud API. Because the model
> is the weak link, smartness comes from **deterministic scaffolding around the
> model**, not from the model itself.

---

## 1. Current architecture (as-is)

```
frontend (mvp_frontend/) 
  → mvp_api.py  /api/chat
    → sql_agent.py  SQLAgent.execute()
      → run_pipeline()         [currently lives in run_execution_accuracy.py]
          1. llm_extract_filters()   llama3.1:8b → {product_type, line-scan fields}
          2. ChromaDB query          n_results=3, where product_type == ...
          3. generate_sql()          llama3.1:8b + glossary prompt
          4. SQLValidator            sqlglot AST: read-only + table/column grounding
          5. self-healing loop       up to 2 retries on validator error
      → execute_sql_safely()   psycopg2 (read-only) → Supabase schema `ragav`
    → synthesize_response()    llama3.1:8b turns rows into prose
```

- **Data:** ~38 Postgres tables (`ragav`), one per lens family/sub-family, all keyed on `model_name`.
- **Knowledge base:** `docs/*.md` (per-table schema docs) → `generate_chunks.py` → `chroma_chunks.json` → `ingest_chroma.py` → ChromaDB (`lens_schema_rag`).
- **Validator allow-list:** `schema_registry.json` (table → columns).

### Priority spec columns (must handle robustly, any phrasing)
model name · focal length (`focus_length_mm`) · price (`list_price`/`price_usd`) ·
f-number (`f_no_min`/`f_no_max`/`f_no_value`) · mount (`mount_raw`) · angles
(`angle_*`) · weight (`weight_g`) · size (`size_diameter_mm`/`size_length_*`) ·
sensor (`sensor_*_raw`) · working distance (`wd_mm`/`wd_min_mm`/`wd_max_mm`) ·
magnification (`magnification_*`) · FOV (`fov_*` — many shapes) · O/I (`o_i`) ·
DOF (`dof_*`) · aperture (= f-number) · TTL (`ttl`/`ttl_*_mm`) · measurement of
object (`measurement_object_diameter_*`) · measurement of height
(`measurement_height_*`).

---

## 2. Root-cause diagnosis — why it isn't smart

| # | Problem | Consequence |
|---|---------|-------------|
| 1 | **No `model_name → table` index exists anywhere.** | Bare model queries (*"MV11051B fov?"*) cannot be routed. This is the #1 blocker. |
| 2 | Routing is **one-dimensional** (`product_type` only) and only fires when the family is stated. | Implicit / attribute-only / model-name queries get no filter → fall back to weak semantic search. |
| 3 | `n_results=3` over **38 tables**. | Right table often not retrieved; cross-table/comparison (UNION) queries impossible — they need every relevant table in context. |
| 4 | A model number has almost **no embedding signal**. | Vector search can't find the table holding a model. |
| 5 | FOV / f-no / wd are stored in **many differently-shaped columns** per table. | "fov?" is ambiguous without knowing the table + sensor format. |
| 6 | Reasoning done by **llama3.1:8b**. | Limited multi-step reasoning; needs scaffolding + a stronger *local* SQL model. |
| 7 | Production imports `run_pipeline` from an **eval script**. | Fragile structure; hard to evolve. |
| 8 | **Currency bug:** `mvp_api.py` says `list_price` = INR (₹); every `docs/*.md` says USD. | Wrong answers today. |

---

## 3. Redundant / stale files

| File | Verdict |
|------|---------|
| `generate_sql.py` | **Delete** — dead prototype (hard-coded query, qwen2.5-coder), superseded by `run_pipeline()`. |
| `query_chroma.py` | **Delete** — dev scratch, hard-coded query. (Fold into debug tool if useful.) |
| `README.md` | **Rewrite** — currently describes only ingestion; badly stale. |
| `run_full_evaluation.py` + `evaluation_dataset.json` | **Merge** into the single eval harness (overlaps `run_execution_accuracy.py` + `golden_dataset.json`). |
| `evaluation_charts.png`, `evaluation_report.csv`, `evaluation_notebook.ipynb` | **Gitignore** — generated artifacts, shouldn't be committed. |
| `create_all_lenses_view.sql` | Keep but **complete** — only covers some tables today; superseded conceptually by the model index (Phase 1). |
| `run_sql_agent_debug.py` | **Keep** — valuable 5-stage trace tool. |

---

## 4. Implementation plan (local-first)

Ordered by impact. **Phases 1–2 alone fix the model-name case and most
"however-worded" queries.** Because we're staying local, each phase leans on
deterministic logic so the 8B model has to reason as little as possible.

### Phase 0 — Restructure (no behavior change)
- [ ] Extract the pipeline into **`pipeline.py`** (`extract_filters`, `route`, `retrieve_context`, `generate_sql`, `run_pipeline`). `sql_agent.py` + all eval scripts import from it. Eval scripts stop being load-bearing.
- [ ] Delete `generate_sql.py`, `query_chroma.py`; gitignore generated artifacts; rewrite `README.md`.
- [ ] **Fix the currency bug** — pick one source of truth (docs say USD), make `mvp_api.py` synthesis prompt agree, add a single `CURRENCY` constant.

### Phase 1 — Model-name resolution layer  *(fixes "MV11051B fov?")*
Highest leverage. Pure scaffolding — no model smartness needed.
- [ ] **Build a model index.** One scan of every table → `model_index.json` (or a `ragav.model_catalog` view): `model_name → {table, family}` plus a few headline specs. ~thousands of tiny rows. Add a `build_model_index.py` that regenerates it (run after any data refresh).
- [ ] **Model-token detection + lookup at query time.** Regex for catalog-style alphanumerics (e.g. `MV11051B`), plus **fuzzy match** (rapidfuzz) for typos/partials (`MV1105`, `mv 11051 b`). On hit → route **directly** to the model's table, skipping semantic guessing.
- [ ] **Multi-model queries.** If 2+ models named → route to each table; if different tables → generate a UNION. Enables *"compare MV11051B and MV12080 weight"*.

### Phase 2 — Deterministic router + stronger local SQL model
Replaces the brittle `product_type`-only filter.
- [ ] **Table-catalog router.** Maintain a compact one-line catalog of all 38 tables (purpose + key columns) — small enough to put fully in the prompt. Router step (rules first, LLM fallback) selects **candidate table(s)**; ChromaDB then pulls the **full schema doc** only for those tables. Handles implicit-family + cross-family queries that the current 3-chunk window can't.
- [ ] **Raise `n_results` / retrieve-by-chosen-tables** so UNION/comparison queries see every relevant table.
- [ ] **Upgrade the local generation model** (the real smartness bottleneck). Evaluate, hardware permitting:
  - `qwen2.5-coder:14b` / `:32b` — strong at SQL, likely the best local pick.
  - `llama3.1:70b` if the box can run it.
  - Keep `llama3.1:8b` as the cheap router/intent model.
  Benchmark each against the Phase 4 eval suite before committing.

### Phase 3 — Semantic spec mapping (the "however worded" part)
- [ ] **Data-driven synonym → column map, keyed per table** (since `fov`/`f_no`/`wd` differ per table). Replaces the hand-written inline glossary in the prompt. Encodes: units, `*_operator` companion columns, `ABS()` for distortion, NULL-filtering for superlatives, "aperture" = f-number, etc.
- [ ] **FOV/ambiguity disambiguation.** "fov?" on a multi-sensor telecentric table → return all sensor-format FOVs **or** state the assumed sensor. Generalize to any spec that has per-sensor/min-max variants.
- [ ] **Intent classifier** (lookup / filter / superlative / count / compare / spec-dump / out-of-scope) — cheap 8B call or rules. Adapts prompt + output shape; improves consistency.
- [ ] **Graceful ambiguity + scope handoff.** Under-specified → pick sensible default and **state the assumption** (or ask one clarifying question). Calculation/website questions → signal the orchestrator to hand off to the calc/domain agents (out of SQA scope, but SQA must recognize and decline cleanly).

### Phase 4 — Evaluation that proves smartness
- [ ] `golden_dataset.json` is 100% explicit-family queries → can't measure the improvement. **Add suites for:** bare model-name lookups (*"MV11051B fov?"*), implicit-family, multi-spec, model-vs-model comparison, count/aggregate, ambiguous, and out-of-scope. This is the regression net for the model swap.
- [ ] **Consolidate** the two eval harnesses into one; keep `run_sql_agent_debug.py`.
- [ ] Track accuracy per query-type so we can see exactly which categories the new scaffolding unlocks.

---

## 5. Target architecture (to-be)

```
pipeline.run_pipeline(user_query)
  1. intent + entity pass        → {intent, model_names[], family?, specs[]}
  2. ROUTER (deterministic-first):
        model_names? → model_index → table(s)        [Phase 1]
        else family/attribute? → table-catalog router [Phase 2]
  3. retrieve full schema doc(s) for chosen table(s)   [Phase 2]
  4. spec map: expand synonyms → exact columns/operators [Phase 3]
  5. generate SQL (qwen2.5-coder local)                [Phase 2]
  6. SQLValidator + self-healing loop                  [unchanged]
  7. execute (read-only) → normalize → synthesize
```

---

## 6. Open items / dependencies
- **Local hardware ceiling** decides which generation model in Phase 2 (14b vs 32b vs 70b). Confirm available VRAM/RAM.
- **Currency:** confirm USD (per docs) is correct before Phase 0 fix ships.
- **Model index freshness:** needs a rebuild step whenever Supabase data is re-ingested.
- **Orchestrator contract:** how SQA signals "this belongs to the calc/domain agent" — coordinate with teammates.
```
