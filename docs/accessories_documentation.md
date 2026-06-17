# Table: adapters

## Purpose

Stores specifications for **lens mount adapters** — mechanical accessories used in machine vision and industrial imaging systems to bridge incompatible mount standards between lenses and cameras. Adapters allow a lens with one mount type (e.g., F-mount) to be physically and optically coupled to a camera body with a different mount type (e.g., C-mount). This table supports engineering lookups for mount compatibility checks and physical integration planning in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the adapter model | text | Primary key. Used as the main lookup key across all queries. |
| mount_primary_raw | Raw text describing the primary (lens-side) mount type | text | Determines which lens mounts can be accepted. Use `ILIKE` for pattern matching (e.g., 'F-mount', 'M42'). |
| mount_secondary_raw | Raw text describing the secondary (camera-side) mount type | text | Determines which camera bodies are compatible. Use `ILIKE` for pattern matching (e.g., 'C-mount', 'CS-mount'). |
| length_mm | Physical length of the adapter in millimeters | numeric | Affects the total optical path length and back focal distance. Critical for focus confirmation. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `adapters` ↔ `extension_rings`, `focusing_rings`, `lens_holders`
* All accessories tables share `mount_primary_raw` and `mount_secondary_raw` columns, enabling cross-table mount compatibility lookups.
* Adapters are commonly paired with extension rings or focusing rings to fine-tune optical path length after mount conversion.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the mount types and lengths of all available adapters?

Reasoning:
- Select all identifying and specification columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM adapters;
```

---

**2. Mount Compatibility Filter**

Natural Language:
Find all adapters that connect an F-mount lens to a C-mount camera.

Reasoning:
- Filter `mount_primary_raw` for F-mount (lens side).
- Filter `mount_secondary_raw` for C-mount (camera side).
- Use `ILIKE` to handle format variations.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM adapters
WHERE mount_primary_raw ILIKE '%F%'
  AND mount_secondary_raw ILIKE '%C%';
```

---

**3. Length-Based Filtering**

Natural Language:
Which adapters have a length of less than 10 mm?

Reasoning:
- Filter on `length_mm` for compact adapters suitable for tight installations.

```sql
SELECT model_name, length_mm, mount_primary_raw, mount_secondary_raw
FROM adapters
WHERE length_mm < 10;
```

---

**4. Camera-Side Mount Lookup**

Natural Language:
List all adapters compatible with a C-mount camera body.

Reasoning:
- Filter `mount_secondary_raw` for C-mount.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM adapters
WHERE mount_secondary_raw ILIKE '%C%';
```

---

## Notes

- **Primary Key:** `model_name`
- `mount_primary_raw` and `mount_secondary_raw` are free-text fields; always use `ILIKE` with `%` wildcards for reliable matching.
- `length_mm` directly affects back focal distance when inserted into an optical assembly; always account for adapter length when calculating total conjugate distance.
- This table is optimized for RAG chunk retrieval when queries mention "adapter", "mount conversion", "lens-to-camera compatibility", or specific mount type pairings.

---

---

# Table: extension_rings

## Purpose

Stores specifications for **extension rings** (also called extension tubes) — passive optical accessories inserted between a lens and a camera body to increase the lens-to-sensor distance, enabling closer focus and higher magnification. Extension rings are widely used in macro and micro inspection applications, PCB inspection, and semiconductor imaging. This table supports engineering lookups for mount compatibility and optical path extension planning in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the extension ring model | text | Primary key. Used as the main lookup key across all queries. |
| mount_primary_raw | Raw text describing the primary (lens-side) mount type | text | Determines which lens mounts are accepted. Use `ILIKE` for pattern matching. |
| mount_secondary_raw | Raw text describing the secondary (camera-side) mount type | text | Determines which camera bodies are compatible. Use `ILIKE` for pattern matching. |
| length_mm | Physical length of the extension ring in millimeters | numeric | Directly determines how much the optical path is extended. Longer rings yield higher magnification at the cost of reduced working distance. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `extension_rings` ↔ `adapters`, `focusing_rings`, `lens_holders`
* Shares mount type columns with all other accessories tables, enabling cross-accessory compatibility lookups.
* Extension rings are frequently stacked or combined with adapters to achieve precise working distance and magnification targets.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all extension rings with their mount types and lengths.

Reasoning:
- Select all columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM extension_rings;
```

---

**2. Mount Compatibility Filter**

Natural Language:
Which extension rings are compatible with a C-mount lens and camera?

Reasoning:
- Filter both mount columns for C-mount to find rings usable in a pure C-mount assembly.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM extension_rings
WHERE mount_primary_raw ILIKE '%C%'
  AND mount_secondary_raw ILIKE '%C%';
```

---

**3. Length-Based Selection**

Natural Language:
Find all extension rings longer than 20 mm for high-magnification setups.

Reasoning:
- Filter `length_mm` for longer rings that increase magnification significantly.

```sql
SELECT model_name, length_mm, mount_primary_raw, mount_secondary_raw
FROM extension_rings
WHERE length_mm > 20;
```

---

**4. Short Ring Lookup**

Natural Language:
Which extension rings have a length of 5 mm or less for minimal optical path change?

Reasoning:
- Filter `length_mm` for very short rings used for fine-tuning focus.

```sql
SELECT model_name, length_mm, mount_primary_raw, mount_secondary_raw
FROM extension_rings
WHERE length_mm <= 5;
```

---

## Notes

- **Primary Key:** `model_name`
- `mount_primary_raw` and `mount_secondary_raw` use free-text format; always query with `ILIKE` and `%` wildcards.
- `length_mm` is the key optical parameter: adding extension increases magnification but reduces working distance and light throughput.
- Multiple extension rings can be stacked; sum their `length_mm` values to determine total optical path extension.
- This table is optimized for RAG chunk retrieval when queries mention "extension ring", "extension tube", "macro extension", "magnification increase", or "working distance reduction".

---

---

# Table: focusing_rings

## Purpose

Stores specifications for **focusing rings** — adjustable mechanical accessories inserted between a lens and a camera body to allow fine-tuning of focus position and working distance. Unlike fixed extension rings, focusing rings provide a continuous range of length adjustment, making them suitable for applications where precise focus must be achieved at variable working distances. They are commonly used in macro inspection, flat panel display inspection, and semiconductor metrology. This table supports engineering lookups for mount compatibility, adjustable length ranges, and focal length association in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the focusing ring model | text | Primary key. Used as the main lookup key across all queries. |
| mount_primary_raw | Raw text describing the primary (lens-side) mount type | text | Determines which lens mounts are accepted. Use `ILIKE` for pattern matching. |
| mount_secondary_raw | Raw text describing the secondary (camera-side) mount type | text | Determines which camera bodies are compatible. Use `ILIKE` for pattern matching. |
| length_min_mm | Minimum physical length of the focusing ring at its shortest adjustment position | numeric | Lower bound of the adjustable range. Units: mm. |
| length_max_mm | Maximum physical length of the focusing ring at its longest adjustment position | numeric | Upper bound of the adjustable range. Units: mm. |
| combination_length_mm | Total optical path length when the focusing ring is used in a standard combination assembly | numeric | Useful for planning full accessory stack lengths. Units: mm. |
| focus_length_mm | Focal length of the lens this focusing ring is designed or optimized for | numeric | Used to match focusing rings to specific lens focal lengths. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `focusing_rings` ↔ `adapters`, `extension_rings`, `lens_holders`
* `focus_length_mm` logically links to `focus_length_mm` in lens tables (e.g., `coaxial_illumination_line_scan_lens`, `line_scan_lens_*` families) for matched-pairing queries.
* Mount columns are shared across all accessories tables for cross-compatibility filtering.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the adjustment range and focal length of all focusing rings?

Reasoning:
- Select the identifying column and the key specification columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, length_min_mm, length_max_mm, combination_length_mm, focus_length_mm
FROM focusing_rings;
```

---

**2. Focal Length Match**

Natural Language:
Which focusing rings are designed for a 50 mm focal length lens?

Reasoning:
- Filter on `focus_length_mm` to find rings matched to a specific lens focal length.

```sql
SELECT model_name, focus_length_mm, mount_primary_raw, mount_secondary_raw, length_min_mm, length_max_mm
FROM focusing_rings
WHERE focus_length_mm = 50;
```

---

**3. Adjustment Range Filter**

Natural Language:
Find focusing rings with an adjustment range of at least 10 mm (i.e., difference between max and min length is ≥ 10 mm).

Reasoning:
- Compute the difference between `length_max_mm` and `length_min_mm` to find rings with wide focus travel.

```sql
SELECT model_name, length_min_mm, length_max_mm,
       (length_max_mm - length_min_mm) AS adjustment_range_mm
FROM focusing_rings
WHERE (length_max_mm - length_min_mm) >= 10;
```

---

**4. Mount Compatibility Filter**

Natural Language:
List all focusing rings compatible with a C-mount camera body.

Reasoning:
- Filter `mount_secondary_raw` for C-mount.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, focus_length_mm
FROM focusing_rings
WHERE mount_secondary_raw ILIKE '%C%';
```

---

**5. Combination Length Lookup**

Natural Language:
Which focusing rings have a combination assembly length under 30 mm?

Reasoning:
- Filter `combination_length_mm` for compact total stack assemblies.

```sql
SELECT model_name, combination_length_mm, length_min_mm, length_max_mm
FROM focusing_rings
WHERE combination_length_mm < 30;
```

---

## Notes

- **Primary Key:** `model_name`
- `length_min_mm` and `length_max_mm` define the continuous adjustment travel of the ring; the difference gives the total focus travel range.
- `combination_length_mm` represents the total optical path contributed by the ring in a standard assembly — use this when calculating overall system stack length.
- `focus_length_mm` is used to match a focusing ring to its intended lens; cross-reference with lens tables using this column.
- `mount_primary_raw` and `mount_secondary_raw` are free-text; always query with `ILIKE`.
- This table is optimized for RAG chunk retrieval when queries mention "focusing ring", "adjustable extension", "variable working distance", "focus travel", or "fine focus adjustment".

---

---

# Table: lens_holders

## Purpose

Stores specifications for **lens holders** — mechanical mounting accessories used to physically secure and position lenses within an optical assembly or machine vision system. Lens holders provide structural support and precise alignment of the lens relative to the camera sensor and illumination source. They are commonly used in telecentric lens assemblies, coaxial illumination setups, and custom integration fixtures. This table supports engineering lookups for mount compatibility and physical length planning in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens holder model | text | Primary key. Used as the main lookup key across all queries. |
| mount_primary_raw | Raw text describing the primary (lens-side) mount type | text | Determines which lens mounts are accepted. Use `ILIKE` for pattern matching. |
| mount_secondary_raw | Raw text describing the secondary (camera or fixture-side) mount type | text | Determines which camera bodies or fixtures are compatible. Use `ILIKE` for pattern matching. |
| length_mm | Physical length of the lens holder in millimeters | numeric | Affects total assembly height and clearance requirements. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `lens_holders` ↔ `adapters`, `extension_rings`, `focusing_rings`
* Shares mount type columns with all other accessories tables, enabling cross-accessory mount compatibility lookups.
* Lens holders are often used in combination with adapters or extension rings to build complete optical mounting assemblies.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all lens holders with their mount types and lengths.

Reasoning:
- Select all columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM lens_holders;
```

---

**2. Mount Compatibility Filter**

Natural Language:
Which lens holders are compatible with a C-mount lens?

Reasoning:
- Filter `mount_primary_raw` for C-mount on the lens side.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM lens_holders
WHERE mount_primary_raw ILIKE '%C%';
```

---

**3. Length-Based Filtering**

Natural Language:
Find all lens holders with a length greater than 25 mm.

Reasoning:
- Filter `length_mm` for longer holders needed in assemblies with additional clearance requirements.

```sql
SELECT model_name, length_mm, mount_primary_raw, mount_secondary_raw
FROM lens_holders
WHERE length_mm > 25;
```

---

**4. Cross-Mount Holder Lookup**

Natural Language:
Which lens holders connect an M42 lens to a C-mount fixture?

Reasoning:
- Filter `mount_primary_raw` for M42 and `mount_secondary_raw` for C-mount.

```sql
SELECT model_name, mount_primary_raw, mount_secondary_raw, length_mm
FROM lens_holders
WHERE mount_primary_raw ILIKE '%M42%'
  AND mount_secondary_raw ILIKE '%C%';
```

---

## Notes

- **Primary Key:** `model_name`
- `mount_primary_raw` and `mount_secondary_raw` are free-text fields; always use `ILIKE` with `%` wildcards for reliable matching.
- `length_mm` contributes to the total optical assembly stack height; account for it when computing total conjugate distance or clearance.
- Lens holders differ from adapters in their primary function: adapters convert mount standards, while lens holders provide structural fixturing and alignment.
- This table is optimized for RAG chunk retrieval when queries mention "lens holder", "lens mount fixture", "optical assembly support", "lens positioning", or "structural mount".

---
