# Calculator Router MCP — Skills Reference

Server exposes **6 tools**. Start with `search`, then drill down.

---

## Starting the server

```bash
cd "experiments/MCP with less tools"
python server.py
# SSE →  http://0.0.0.0:8001/sse
# Health → http://0.0.0.0:8001/health
```

---

## The 6 Tools

### 1. `search`

Finds relevant calculators from a natural language question.
Uses tag index + BM25 — no embeddings needed.

```python
search(
    query: str,
    top_k: int = 10,    # how many results
    category: str = ""  # filter: "optics", "sensor", "metrology",
                        #         "reference", "motion", or "" for all
)
```

**Returns** a ranked list of matches:
```json
{
  "results": [
    {
      "parent_id": "measurement_accuracy",
      "score": 110.0,
      "category": "metrology",
      "tool_name": "measurement_accuracy",
      "sections": ["purpose", "explanation", "use_cases", "example_queries", "input_meanings", "gotchas", "related_calculators"]
    }
  ]
}
```

- `parent_id` — use this in `get_parent()`, `get_related()`, `calculate()`
- `tool_name` — null for reference tables (f-stops, sensor sizes, etc.) — those can't be calculated, only looked up
- `score` — higher is more relevant; 100+ means exact ID or tag hit

**Examples:**
```python
search("can I measure a 0.05 mm scratch")
search("what focal length lens do I need for 300 mm object")
search("line scan camera line rate conveyor speed")
search("how many bytes per pixel is Mono 8", category="reference")
search("sensor diagonal from resolution and pixel size")
```

---

### 2. `get_parent`

Gets the full knowledge document for a calculator — purpose, formula, examples, gotchas, inputs explained.

```python
get_parent(parent_id: str)
```

**Returns:**
```json
{
  "id": "depth_of_field",
  "category": "optics",
  "tool_name": "depth_of_field",
  "required_inputs": ["working_distance_mm", "pixel_size_um", "focal_length_mm", "f_number"],
  "optional_inputs": [],
  "related": ["exposure_time", "focal_length"],
  "sections": {
    "purpose": "...",
    "explanation": "...",
    "use_cases": "...",
    "example_queries": "...",
    "input_meanings": "...",
    "gotchas": "...",
    "related_calculators": "..."
  }
}
```

**Examples:**
```python
get_parent("depth_of_field")
get_parent("sensor_geometry")
get_parent("f_stop_values")          # reference table — no tool_name
get_parent("pixel_format_bytes")     # reference table — bytes per pixel lookup
```

---

### 3. `get_related`

Returns graph neighbors — calculators that feed into or depend on a given one.
Use for multi-step planning when inputs are missing.

```python
get_related(parent_id: str)
```

**Returns:**
```json
{
  "parent_id": "sensor_geometry",
  "related": ["fov_using_pixel_size", "fov_using_sensor_size", "focal_length", "o_ring"]
}
```

**Multi-hop planning example:**
```
Need focal_length
  → get_related("focal_length")
  → sees sensor_geometry is related
  → run sensor_geometry first (width_pixels + height_pixels + pixel_size_um)
  → use sensor_width_mm output as sensor_size_mm input for focal_length
```

---

### 4. `list_inputs`

Lists what a calculator needs before you call it.

```python
list_inputs(formula_id: str)
```

**Returns:**
```json
{
  "required": ["working_distance_mm", "pixel_size_um", "focal_length_mm", "f_number"],
  "optional": []
}
```

**Examples:**
```python
list_inputs("depth_of_field")
list_inputs("fov_using_pixel_size")
list_inputs("line_scan_frequency")
```

---

### 5. `validate_inputs`

Pre-flight check: tells you which required inputs you're still missing.

```python
validate_inputs(
    formula_id: str,
    args: dict          # inputs you currently have
)
```

**Returns:**
```json
{ "valid": false, "missing": ["sensor_size_mm"] }
{ "valid": true,  "missing": [] }
```

**Example:**
```python
validate_inputs("focal_length", {
    "object_size_mm": 300,
    "working_distance_mm": 500
    # sensor_size_mm is missing
})
# → {"valid": false, "missing": ["sensor_size_mm"]}
```

---

### 6. `calculate`

Runs the formula and returns results.

```python
calculate(
    formula_id: str,
    args: dict
)
```

**Example:**
```python
calculate("focal_length", {
    "object_size_mm": 300,
    "working_distance_mm": 500,
    "sensor_size_mm": 8.8
})
# → {"focal_length_mm": 14.2, "valid": true, "warning": null}
```

---

## Available formula_ids

| formula_id | What it calculates |
|---|---|
| `fov_using_pixel_size` | Sensor geometry + H/V/diagonal FOV from pixel count + pixel size |
| `fov_using_sensor_size` | FOV from physical sensor size (mm) |
| `working_distance_using_pixel_size` | Camera distance for desired FOV, via pixel count + pixel size |
| `working_distance_using_sensor_size` | Camera distance for desired FOV, via sensor size (mm) |
| `focal_length` | Required lens focal length |
| `depth_of_field` | Near/far focus limits, total DOF |
| `exposure_time` | Max exposure before motion blur exceeds N pixels |
| `line_scan_frequency` | Line rate, resolution, data throughput for line scan |
| `measurement_accuracy` | Achievable measurement precision in mm |
| `o_ring` | Extension ring requirement and length |
| `sensor_geometry` | Physical sensor dimensions + aspect ratio from pixels + pitch |

---

## Reference tables (search only — no `calculate`)

| parent_id | Contents |
|---|---|
| `f_stop_values` | f/1 to f/22 exact decimal values |
| `pixel_format_bytes` | Mono8, RGB24, Mono12, etc. → bytes/pixel |
| `sensor_format_sizes` | 1/4" to Full Frame → diagonal mm |
| `line_scan_sensor_widths` | 0.5K–12K line scan sensors → physical width mm |

---

## Typical agent workflow

```
User: "Can I measure a 0.1 mm scratch with my 2448×2048 camera at 200 mm FOV?"

1. search("measure 0.1 mm scratch 2448x2048 200mm FOV")
   → top hit: measurement_accuracy

2. list_inputs("measurement_accuracy")
   → required: object_size_mm, sensor_pixels, nyquist_factor, subpixel_factor

3. validate_inputs("measurement_accuracy", {"object_size_mm": 200, "sensor_pixels": 2448})
   → missing: nyquist_factor, subpixel_factor

4. # Ask user or use defaults (nyquist=2, subpixel=0.5)

5. calculate("measurement_accuracy", {
       "object_size_mm": 200,
       "sensor_pixels": 2448,
       "nyquist_factor": 2,
       "subpixel_factor": 0.5
   })
   → {"measurement_accuracy_mm": 0.082, "mm_per_pixel": 0.0818, "valid": true}

6. Answer: "Yes — your system achieves ~0.082 mm accuracy, which can resolve a 0.1 mm scratch."
```

---

## Multi-step workflow (sensor_geometry feeding focal_length)

```
User: "What lens do I need for a 2448×2048 sensor at 3.45 µm to cover 300 mm at 500 mm?"

1. search("focal length lens 2448x2048 3.45um 300mm")
   → focal_length, sensor_geometry

2. get_related("focal_length")
   → ["sensor_geometry", "fov_using_sensor_size", ...]
   # focal_length needs sensor_size_mm — get it from sensor_geometry first

3. calculate("sensor_geometry", {
       "width_pixels": 2448, "height_pixels": 2048, "pixel_size_um": 3.45
   })
   → {"width_mm": 8.45, "height_mm": 7.07, ...}

4. calculate("focal_length", {
       "object_size_mm": 300,
       "working_distance_mm": 500,
       "sensor_size_mm": 8.45
   })
   → {"focal_length_mm": 14.08, "valid": true}

5. Answer: "You need approximately a 14 mm lens."
```