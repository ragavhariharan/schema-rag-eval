# Table: macro_lenses

## Purpose

Stores specifications for **macro lenses** — close-focus, high-magnification machine vision lenses designed to image small objects or fine details at reproduction ratios at or near 1:1 (life-size) and beyond. Macro lenses are used in applications including electronics component inspection, solder joint analysis, pharmaceutical tablet inspection, biological specimen imaging, micro-engraving verification, watch and jewelry inspection, and any task where the object or feature of interest is small enough to require magnification greater than what standard FA lenses provide at practical working distances.

This table supports engineering lookups for selecting macro lenses by focal length, magnification range, working distance, object-to-image distance, aperture, sensor size, filter thread, mount type, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. For macro lenses, focal length determines working distance at a given magnification. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string (e.g., "F2.8 – F22"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. Depth of field is very shallow at macro distances. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. Diffraction limits the effective sharpness at very high F-numbers in macro. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel; positive = pincushion. Macro lenses are typically optimized for very low distortion. Use `ABS()` for magnitude comparisons. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string (e.g., "0.5× – 2×"). Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. E.g., 0.5 = half life-size. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. E.g., 2.0 = twice life-size. Values ≥ 1 are true macro. |
| object_image_distance_raw | Raw text for the total object-to-image (conjugate) distance specification | text | Original source string. Preserved for display. |
| object_image_distance_min_mm | Minimum total object-to-image distance in millimeters | numeric | Shortest total optical path from object to sensor. Units: mm. |
| object_image_distance_max_mm | Maximum total object-to-image distance in millimeters | numeric | Longest total optical path from object to sensor. Units: mm. |
| wd_raw | Raw text representation of the working distance range | text | Original source string. Preserved for display. |
| wd_min_mm | Minimum working distance in millimeters | numeric | Closest operational distance from lens front to target. Units: mm. |
| wd_max_mm | Maximum working distance in millimeters | numeric | Farthest operational distance from lens front to target. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M52×0.75". Use `ILIKE` for matching. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Length at closest focus / highest magnification. Units: mm. |
| size_length_max_mm | Maximum physical length of the lens body in millimeters | numeric | Length at farthest focus / lowest magnification. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `macro_lenses` ↔ `microscope_lenses`: both serve high-magnification imaging. Macro lenses are typically used at magnifications from ~0.5× to ~5×; microscope lenses (objectives + tube lens) cover higher magnifications. Cross-reference by `magnification_max` to determine which family is appropriate.
* `macro_lenses` ↔ `motorized_bi_telecentric_lenses`: telecentric lenses also serve precision measurement at macro magnifications; cross-compare by `magnification_min`, `magnification_max`, and `wd_mm`.
* `object_image_distance_*` columns are analogous to `o_i` in `large_format_lenses` and `coaxial_illumination_line_scan_lens` for total conjugate distance planning.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all macro lenses with their focal length, magnification range, and working distance range.

Reasoning:
- Select identifying and key optical specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, focus_length_mm, magnification_min, magnification_max,
       wd_min_mm, wd_max_mm
FROM macro_lenses;
```

---

**2. True Macro Filter (Magnification ≥ 1×)**

Natural Language:
Which macro lenses support true macro magnification of 1× or greater?

Reasoning:
- Filter `magnification_max` for lenses that reach or exceed 1:1 reproduction ratio.

```sql
SELECT model_name, magnification_min, magnification_max, magnification_raw,
       wd_min_mm, focus_length_mm
FROM macro_lenses
WHERE magnification_max >= 1.0;
```

---

**3. Working Distance Filter**

Natural Language:
Find macro lenses with a minimum working distance of at least 50 mm for easier access to the subject.

Reasoning:
- Filter `wd_min_mm` for lenses with enough front-to-subject clearance to avoid lighting and handling obstructions.

```sql
SELECT model_name, wd_min_mm, wd_max_mm, magnification_max, focus_length_mm
FROM macro_lenses
WHERE wd_min_mm >= 50;
```

---

**4. Magnification Range Overlap**

Natural Language:
Which macro lenses can achieve a magnification of 1.5×?

Reasoning:
- Filter for lenses where the target magnification (1.5×) falls within the supported range.

```sql
SELECT model_name, magnification_min, magnification_max, wd_min_mm, wd_max_mm
FROM macro_lenses
WHERE magnification_min <= 1.5
  AND magnification_max >= 1.5;
```

---

**5. Distortion Filter**

Natural Language:
List all macro lenses with TV distortion below 0.5% for precision measurement applications.

Reasoning:
- Use `ABS()` to handle signed distortion values; macro measurement lenses should have very low distortion.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, focus_length_mm
FROM macro_lenses
WHERE ABS(tv_distortion_percent) < 0.5;
```

---

**6. Object-to-Image Distance Filter**

Natural Language:
Find macro lenses with a maximum object-to-image distance under 300 mm for compact system integration.

Reasoning:
- Filter `object_image_distance_max_mm` for lenses with short total conjugate distances.

```sql
SELECT model_name, object_image_distance_min_mm, object_image_distance_max_mm,
       focus_length_mm, magnification_max
FROM macro_lenses
WHERE object_image_distance_max_mm < 300;
```

---

**7. Aperture and Magnification Combined**

Natural Language:
Which macro lenses support magnification of at least 2× and have a minimum F-number of 4 or lower?

Reasoning:
- Combine `magnification_max` and `f_no_min` filters for high-magnification lenses with reasonable light-gathering ability.

```sql
SELECT model_name, magnification_max, f_no_min, f_no_raw, wd_min_mm
FROM macro_lenses
WHERE magnification_max >= 2.0
  AND f_no_min <= 4;
```

---

**8. Mount and Size Filter**

Natural Language:
List C-mount macro lenses weighing less than 300 grams.

Reasoning:
- Combine `mount_raw` and `weight_g` filters for lightweight C-mount macro lenses.

```sql
SELECT model_name, mount_raw, weight_g, focus_length_mm, magnification_max
FROM macro_lenses
WHERE mount_raw ILIKE '%C%'
  AND weight_g < 300;
```

---

## Notes

- **Primary Key:** `model_name`
- `magnification_max >= 1.0` is the threshold for "true macro" reproduction (life-size or larger); lenses below this threshold are close-focus but not technically macro.
- `tv_distortion_percent` may be positive or negative; use `ABS()` for magnitude comparisons. Macro and measurement lenses are typically engineered for extremely low distortion.
- `wd_min_mm` is critical for practical usability: very small values (< 10 mm) may obstruct illumination and make specimen handling difficult.
- `object_image_distance_min_mm` and `object_image_distance_max_mm` describe the total optical conjugate distance range, distinct from working distance — use these for full system path length planning.
- `size_length_min_mm` and `size_length_max_mm` reflect physical body length variation across the focus/magnification range (macro lenses extend internally or externally as magnification increases).
- All `*_raw` and `mount_raw` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "macro lens", "close-up lens", "high magnification lens", "1:1 lens", "life-size imaging", "micro inspection lens", or "small object inspection lens".

---
