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

### Phase 0 — Restructure (no behavior change) ✅ DONE
- [x] Extract the pipeline into **`pipeline.py`** (DB connection, retrieval, `llm_extract_filters`, `run_pipeline`). `sql_agent.py` + all eval scripts import from it. Eval scripts stop being load-bearing.
- [x] Delete `generate_sql.py`, `query_chroma.py`; rewrite `README.md`. (generated artifacts gitignore — still TODO)
- [x] **Fix the currency bug** — corrected the docs (the actual source of the error): `list_price` is INR (base USD × markup × dollar-sheet rate), not USD; `price_usd` is the base USD. `mvp_api.py` was already correct.

### Phase 1 — Model-name resolution layer  *(fixes "MV11051B fov?")* ✅ DONE
Highest leverage. Pure scaffolding — no model smartness needed.
- [x] **Build a model index.** `build_model_index.py` scans every model-bearing table → `model_index.json` (`model_name → [{table, product_type}]`). Re-run after any data refresh. *(User must run it once — needs DB access.)*
- [x] **Model-token detection + lookup at query time.** `resolve_models()` in `pipeline.py`: regex for letter+digit tokens → exact, whitespace/case-insensitive lookup → route directly to the model's table. **Fuzzy match (rapidfuzz) deferred** to a later step per decision (exact-first).
- [x] **Multi-model queries.** 2+ models → route to each table; different tables → routing hint instructs `UNION ALL`. Enables *"compare MV11051B and MV12080 weight"*.

### Phase 2 — Deterministic router + stronger local SQL model
Replaces the brittle `product_type`-only filter.
- [x] **Table-catalog router.** `build_table_catalog.py` → `table_catalog.json` (one line per table: purpose + distinctive cols). `router.py` `route_tables()` selects candidate table(s) via the local LLM, validated against real names. Wired into `pipeline.py` as: model-name → table-router → legacy fallback. ✅ Routing verified (implicit-family + cross-family selection works).
- [x] **Retrieve-by-chosen-tables.** Pulls full schema docs for the routed tables; cross-table queries expand to all tables with a compact column-only context (so 32 docs don't blow the context window) + UNION hint.
- [x] **Upgrade the local generation model.** Default `SQL_GEN_MODEL = qwen2.5-coder:7b` (router/filter stay on `llama3.1:8b`; override via env var). A/B showed qwen writes far better SQL than llama (correct wrapped UNION structure), but neither model reliably assembles multi-table UNIONs by hand — so we don't rely on them to.
- [x] **Deterministic UNION-expander** (`multi_table.py`). Model writes ONE single-table query; `expand_to_tables()` replicates it across the routed tables that contain the referenced columns (registry-driven, so tables lacking a column are skipped automatically — no hardcoding), combining with UNION ALL and moving superlative ORDER BY/LIMIT to an outer query. Verified: "cheapest lens overall" now returns the true cheapest (₹4,782) vs the old single-table ₹193,840; "telecentric DOF > 5mm" returns 12 rows across all 4 telecentric tables vs 2.

### Phase 3 — Semantic spec mapping (the "however worded" part)
> ⏳ STARTED EARLY: `column_aliases.py` already handles the DB's column-name
> synonyms (`sensor_raw`/`sensor_size_raw`, `flange_distance`/`flange_distance_mm`,
> `ttl`/`ttl_mm`) and the unit traps (`three_cmos` working distance in metres,
> microscope `dof_um` in microns), injected into the generation prompt per-table.

- [ ] **Data-driven synonym → column map, keyed per table** (since `fov`/`f_no`/`wd` differ per table). Replaces the hand-written inline glossary in the prompt. Encodes: units, `*_operator` companion columns, `ABS()` for distortion, NULL-filtering for superlatives, "aperture" = f-number, etc.
- [ ] **FOV/ambiguity disambiguation.** "fov?" on a multi-sensor telecentric table → return all sensor-format FOVs **or** state the assumed sensor. Generalize to any spec that has per-sensor/min-max variants.
- [ ] **Intent classifier** (lookup / filter / superlative / count / compare / spec-dump) — adapts prompt + output shape. Deferred (the pipeline already handles these shapes well via the prompt + expander).
- [x] **Scope gate / handoff** (`scope.py`). `classify_scope()` labels each query `sql` / `calculation` / `domain` / `chitchat`; `SQLAgent` runs it before the pipeline (model-name queries fast-path straight to `sql`) and returns `status="out_of_scope"` with `route_to` for non-catalog queries; `mvp_api.py` replies with a clean handoff message. Eval: `run_scope_eval.py` → **14/14**. Fast (~1.3s, short-circuits before SQL generation).
- [ ] **Under-specified disambiguation** (state-an-assumption / ask one clarifying question) — still open; the no-results path handles empties for now.

### Phase 4 — Evaluation that proves smartness
- [x] **`smart_eval_dataset.json`** — 11 queries the old dataset couldn't measure: model-name lookups, implicit-family, multi-table (expander), cross-table superlatives, aggregate, multi-model comparison. Each `expected_sql` verified against the live DB. Tagged with `category` for per-type scoring.
- [x] **Harness takes a dataset path** — `python run_execution_accuracy.py smart_eval_dataset.json` (defaults to `golden_dataset.json`). Result-set comparison, no code duplication.
- [ ] Per-category score breakdown in the dashboard (currently per failure-type); add once we see the first run.
- [ ] **Consolidate** the two eval harnesses (`run_full_evaluation.py` overlaps) — deferred.

### Phase 5 — Conversational layer
- [x] **Query understanding** (`conversation.py` `assess_query`). Runs after the scope gate: rewrites the message into a self-contained query (resolving follow-ups via history), asks ONE clarifying question when too vague (`status="needs_clarification"`), and records an `assumption` when it interprets a vague term. Prefers a stated assumption over a question.
- [x] **Multi-turn memory.** `mvp_api` accepts `history`; `mvp_frontend` keeps and sends the running conversation (stateless server).
- [x] **Well-explained answers.** Synthesis prompt upgraded to lead with the assumption, explain why results answer the question, format cleanly, and keep INR/USD correct.
- [ ] **Latency** ⚠️ pre-pipeline now does 2 small-model calls (scope + understanding) before routing/generation. On the M2 Air that's ~6–16s warm (more cold). **Optimization:** merge scope + understanding into ONE call. Deferred.
- [ ] Eval for clarification/assumption behavior (harder — conversational, not result-set). Open.

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
