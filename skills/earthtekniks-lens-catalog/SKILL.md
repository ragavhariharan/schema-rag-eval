---
name: earthtekniks-lens-catalog
description: >-
  Look up, filter, and compare machine-vision LENS PRODUCTS and their stored
  specifications or prices from the EarthTekniks catalog, PLUS a RAG knowledge layer
  that maps a USE CASE to the right lens family. Use whenever the user wants STORED
  product data or guidance on which lens to use: a lens by model name, the cheapest /
  lightest / widest-aperture lens, lenses filtered by focal length, working distance,
  sensor, mount, FOV, magnification, depth of field, telecentricity, weight, or price,
  any spec of a model, OR which lens family fits an application ("what lens to inspect
  a bottle 360 degrees", "measure a flat part without perspective error"). Drives the
  MCP tools search_knowledge, get_table_knowledge, lookup_model, get_product,
  search_products, describe_table, list_families, list_tables, run_select. Use for
  LOOKUPS and lens SELECTION over the catalog, NOT for computing optical values from
  parameters (that is the vision calculator skill).
---

> Prerequisite: the **EarthTekniks Lens Catalog** MCP server must be connected.
> The tools referenced below are exposed by it.

# Lens Catalog MCP — Skills Reference

Server exposes **9 tools** (+1 optional). The catalog is ~38 Postgres tables of lens
**products**, grouped into 15 families, every row keyed on `model_name`.

Typical flow (search → get knowledge → query):
- **Don't know which lens fits a use case?** → `search_knowledge` → `get_table_knowledge`.
- **Have a model name?** → `lookup_model` → `get_product`.
- **Have a table/family + filters?** → `describe_table` → `search_products`, or `run_select`.

> This is a **data** server — it looks up and filters stored lens specs. For
> *computing* engineering values (FOV from focal length, DOF, magnification…),
> that's the **Calculator** MCP, not this one.

---

## Starting the server

```bash
cd schema-rag-eval
python server.py                 # stdio  (Claude Desktop, local clients)
python server.py --http          # HTTP →  http://127.0.0.1:8765/mcp
python server.py --http --port 8765 --host 0.0.0.0
```

Needs `.env` with `DB_*` (Supabase). No DB hit for schema/model lookups — those are
served from in-memory indexes.

> **Running alongside the Calculator MCP on the same machine:** no conflict — that
> server uses port **8001** (SSE), this one uses **8765** (HTTP) or stdio. Register
> both with your orchestrator and route by intent: *compute a value* → Calculator,
> *look up a product/spec/price* → Lens Catalog.

---

## The 8 Tools

### 1. `list_families`

Lists the 15 lens families and the tables in each. Start here to see the catalog.

```python
list_families()
```

**Returns:**

```json
{ "results": [ {"family": "telecentric", "tables": ["standard_telecentric_lenses_1_1_inch", "..."], "table_count": 5} ] }
```

Families: `fa_lens`, `telecentric`, `line_scan`, `macro`, `zoom`, `microscope`,
`spectral`, `m12_mount`, `autofocus`, `large_format`, `three_cmos`, `anti_vibration`,
`laser_coaxial`, `inspection`, `accessory`.

---

### 2. `list_tables`

Tables (optionally one family) with a one-line purpose each.

```python
list_tables(family: str = None)
```

**Returns:** `[ {"table": "fa_lenses", "family": "fa_lens", "purpose": "Factory-automation..."} ]`

**Examples:**

```python
list_tables()
list_tables("telecentric")
```

---

### 3. `describe_table`

Columns, purpose, signature columns, and **unit/synonym caveats** for a table.
Always call this before writing SQL with `run_select`.

```python
describe_table(table: str)
```

**Returns:**

```json
{
  "table": "three_cmos_lenses",
  "family": "three_cmos",
  "purpose": "...",
  "columns": ["model_name", "list_price", "wd_min_m", "..."],
  "signature_columns": ["..."],
  "notes": "UNIT CAVEATS: wd_min_m / wd_max_m are in METRES, not mm. ..."
}
```

**Examples:**

```python
describe_table("fa_lenses")
describe_table("standard_telecentric_lenses_2_3_inch")
describe_table("three_cmos_lenses")   # note the metres caveat
```

---

### 4. `lookup_model`

Resolve a model NAME → its table + family. Exact, case/space-insensitive, and
partial matches; returns `suggestions` when there's no exact hit. No DB hit.

```python
lookup_model(name: str)
```

**Returns:**

```json
{ "query": "FA0401C", "matches": [ {"model_name": "FA0401C", "table": "fa_lenses", "product_type": "fa_lens"} ] }
```

- `matches` empty + `suggestions` present → fuzzy near-misses (e.g. `mv1105` → MV11051A/B)
- a few model names appear in two tables — both are returned

**Examples:**

```python
lookup_model("FA0401C")
lookup_model("mv1105")        # partial → suggestions
```

---

### 5. `get_product`

Full specification row(s) for a specific model. Resolves the table automatically.

```python
get_product(model_name: str)
```

**Returns:**

```json
{ "model": "FA0401C", "results": [ {"table": "fa_lenses", "family": "fa_lens", "row": {"model_name": "FA0401C", "focus_length_mm": 4.0, "list_price": 7208, "...": "..."}} ] }
```

**Examples:**

```python
get_product("FA0401C")
get_product("FS0805A")
```

---

### 6. `search_products`

Filtered search over one `table` or a whole `family` (one is required). When a
family spans several tables, results are combined with `UNION ALL` across every
table that has the requested columns. Whitelisted columns only.

```python
search_products(
    table: str = None,
    family: str = None,
    filters: list = None,      # [{"column": str, "op": str, "value": any}]
    columns: list = None,      # spec columns to return (model_name always included)
    sort: dict = None,         # {"column": str, "direction": "asc"|"desc"}
    limit: int = 50
)
```

Ops: `=`, `!=`, `<`, `<=`, `>`, `>=`, `ILIKE`, `LIKE`, `IS NULL`, `IS NOT NULL`.

**Returns:** `{ "columns": [...], "rows": [...], "row_count": N, "tables_searched": [...], "sql": "..." }`

**Examples:**

```python
search_products(family="telecentric",
                filters=[{"column": "dof_mm", "op": ">", "value": 5}],
                columns=["dof_mm"])

search_products(table="fa_lenses",
                filters=[{"column": "focus_length_mm", "op": ">", "value": 50}],
                columns=["focus_length_mm", "list_price"],
                sort={"column": "list_price", "direction": "asc"}, limit=10)

search_products(family="zoom",
                filters=[{"column": "zoom_type", "op": "ILIKE", "value": "%telecentric%"}],
                columns=["zoom_type"])
```

---

### 7. `search_knowledge`  (RAG: use case → table)

Find which lens table(s)/family fit a USE CASE or NL question. Ranks tables by
relevance over their knowledge docs (purpose + column meanings + example queries).
Dependency-free BM25 — no embeddings. **Start here when you don't know which family
to use**, then `get_table_knowledge` on a hit.

```python
search_knowledge(query: str, top_k: int = 10)
```

**Returns:** `{ "query": "...", "results": [ {"table": "...", "family": "...", "score": 18.3, "purpose": "..."} ] }`

**Examples:**

```python
search_knowledge("measure a flat metal part without perspective error")  # → telecentric
search_knowledge("inspect a bottle 360 degrees")                          # → inspection_360_systems
search_knowledge("image in near-infrared above 1000nm")                   # → spectral
search_knowledge("high magnification close-up of a tiny component")       # → macro / microscope
```

---

### 8. `get_table_knowledge`  (RAG: full table doc)

The rich knowledge for a table — purpose / **when to use this lens type**, every
column's **meaning** (not just its name), worked **example NL→SQL** queries, gotchas,
and related tables. Use to understand a family and how to query it.
(`describe_table` is the lighter columns-only version.)

```python
get_table_knowledge(table: str)
```

**Returns:** `{ "table", "family", "purpose", "columns": [{"name","meaning","datatype","notes"}], "example_queries": [{"question","sql"}], "gotchas", "relationships" }`

**Examples:**

```python
get_table_knowledge("telecentric_lenses_65mp")
get_table_knowledge("inspection_360_systems")
```

> **Superlatives** (cheapest/heaviest/widest overall) are done with `run_select` —
> e.g. UNION the relevant tables and `ORDER BY … LIMIT 1`. (The old `find_extreme`
> tool was retired; SQL covers it.)

---

### 8. `run_select`

Escape hatch: a client-written read-only `SELECT`. Validated first — read-only is
enforced and every table/column must exist (no writes, no DDL, no hallucinated
columns) — then row-capped. Call `describe_table` first for real column names.

```python
run_select(sql: str)
```

**Returns:** `{ "columns": [...], "rows": [...], "row_count": N, "sql": "..." }` or `{ "error": "...", "sql": "..." }`

**Examples:**

```python
run_select("SELECT model_name, list_price FROM macro_lenses "
           "WHERE list_price IS NOT NULL ORDER BY list_price ASC LIMIT 3;")

run_select("SELECT model_name, mount_raw FROM fa_lenses WHERE mount_raw ILIKE '%C%';")
```

---

### (optional) `query_catalog`

Only when the server is started with `ETK_ENABLE_PIPELINE_TOOL=1`. Delegates a whole
natural-language request to the LOCAL pipeline (it understands, routes, writes SQL,
runs it). Use to offload the catalog query to local models instead of composing the
deterministic tools yourself.

```python
query_catalog(request: str, history: list = None)
# → {"sql": "...", "rows": [...], "assumption": "..."}  | {"clarification": "..."} | {"error": "..."}
```

---

## Spec column glossary (whitelisted columns)

| Concept | Column(s) |
|---|---|
| Model name | `model_name` |
| Focal length | `focus_length_mm` |
| **Price (retail)** | `list_price` — **INR (₹)** |
| Price (base) | `price_usd` — **USD**, where present |
| Aperture / F-number | `f_no_min` (widest), `f_no_max`, `f_no_value` |
| Mount | `mount_raw` (use `ILIKE`) |
| Angle of view | `angle_primary_h` / `_v`, `angle_*` |
| Weight | `weight_g` |
| Size | `size_diameter_mm`, `size_length_mm` / `_min_mm` / `_max_mm` |
| Sensor | `sensor_size_raw` **or** `sensor_raw` (same meaning) |
| Working distance | `wd_mm`, or `wd_min_mm`/`wd_max_mm` |
| Magnification | `magnification_min`/`_max`, `magnification_value` |
| FOV | `fov_mm`, `fov_raw`, `fov_d/h/v`, `fov_1_1_inch_h`, `fov_degrees` (varies by table) |
| Depth of field | `dof_mm` (telecentric/zoom), `dof_um` (microscope) |
| TTL | `ttl` **or** `ttl_mm`, `ttl_min_mm`/`_max_mm` |
| Telecentricity | `telecentricity_degrees` |
| Megapixel | `megapixel_rating` |
| Numerical aperture | `numerical_aperture`, `_min`/`_max` |
| Wavelength | `wavelength_min_nm`/`_max_nm`, `wavelength_raw` |
| Measurement (object/height) | `measurement_object_diameter_*`, `measurement_height_*` |

**Unit caveats (also surfaced by `describe_table`):**
- `three_cmos_lenses`: working distance `wd_min_m`/`wd_max_m` is in **METRES** (×1000 to compare with mm).
- `microscope_lenses`: `dof_um` is in **MICRONS** (1 mm = 1000 µm).

**Synonyms (same meaning, different name by table):** `sensor_raw` = `sensor_size_raw`,
`flange_distance` = `flange_distance_mm`, `ttl` = `ttl_mm`.

---

## Typical agent workflow

```
User: "What's the field of view of MV11051B?"

1. lookup_model("MV11051B")
   → table: standard_telecentric_lenses_2_3_inch  (it's a telecentric lens)

2. describe_table("standard_telecentric_lenses_2_3_inch")
   → has FOV across three sensor formats: fov_2_3_inch_*, fov_1_1_8_inch_*, fov_1_2_inch_*

3. get_product("MV11051B")
   → returns the full row incl. all FOV columns

4. Answer: "MV11051B FOV is … (2/3": …, 1/1.8": …, 1/2": …)."
```

```
User: "Cheapest lens overall?"

1. run_select(
     "SELECT model_name, list_price FROM ("
     "  SELECT model_name, list_price FROM fa_lenses WHERE list_price IS NOT NULL "
     "  UNION ALL SELECT model_name, list_price FROM macro_lenses WHERE list_price IS NOT NULL "
     "  /* … UNION the other priced tables (list_families to enumerate) … */"
     ") c ORDER BY list_price ASC LIMIT 1;")
   → FS0305A at ₹4,782

2. Answer: "The cheapest lens in the catalog is FS0305A at ₹4,782."
```

```
User: "What lens should I use to inspect the whole surface of a cylindrical bottle?"

1. search_knowledge("inspect full surface of a cylindrical bottle 360 degrees")
   → inspection_360_systems (top hit)
2. get_table_knowledge("inspection_360_systems")
   → purpose (360° circumferential inspection), columns, example queries
3. search_products(table="inspection_360_systems", columns=["inspection_type","list_price"])
4. Answer with the recommended systems.
```

```
User: "FA lenses under 30 g, lightest first."

1. search_products(table="fa_lenses",
       filters=[{"column":"weight_g","op":"<","value":30}],
       columns=["weight_g"], sort={"column":"weight_g","direction":"asc"})
   → FA1201C 28.7 g, FA2501C 29.3 g, …

2. Answer with the list.
```

```
User: "Telecentric lenses with DOF over 5 mm." (spans 4 telecentric tables)

1. search_products(family="telecentric",
       filters=[{"column":"dof_mm","op":">","value":5}], columns=["dof_mm"])
   → 12 rows, UNION'd across all 4 telecentric tables

2. Answer with the list.
```

```
Anything the structured tools can't express → run_select (after describe_table):

run_select("SELECT model_name, f_no_min, list_price FROM fa_lenses "
           "WHERE f_no_min <= 2.0 AND list_price IS NOT NULL "
           "ORDER BY list_price ASC LIMIT 5;")
```

---

## Notes

- **Currency:** `list_price` is INR (₹); `price_usd` (where present) is the USD base. Never treat as Yen.
- Schema/model lookups (`list_*`, `describe_table`, `lookup_model`) never hit the DB — they're served from in-memory indexes; data fetches are read-only, timeout-bounded, row-capped, and TTL-cached.
- Read-only throughout: `run_select` rejects writes/DDL and ungrounded tables/columns.
