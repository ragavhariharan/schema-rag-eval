# Table: fa_lenses

## Purpose

Stores specifications for **FA (Factory Automation) lenses** — the standard workhorse lens category in industrial machine vision. FA lenses are designed for fixed-focus, high-resolution imaging in quality control, dimensional measurement, barcode reading, OCR, surface inspection, and general automated visual inspection on production lines. They are optimized for compatibility with area scan cameras, offer high resolving power rated in megapixels, and are built to withstand industrial environments.

This table supports engineering lookups for selecting FA lenses by focal length, megapixel rating, aperture, working distance, sensor size compatibility, field of view angles, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Longer focal length = narrower FOV and greater working distance. Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. In the source price list this is the base USD price × markup × the live USD→INR dollar rate (~95.5). |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| megapixel_rating | Optical resolving power rating of the lens in megapixels | integer | Indicates the maximum sensor resolution the lens can support without becoming the resolving bottleneck. E.g., 5, 12, 20. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string (e.g., "F1.4 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel distortion; positive = pincushion. Use `ABS()` for magnitude-only comparisons. |
| mod_raw | Raw text for the Minimum Object Distance specification | text | Original source string. Preserved for display. |
| mod_distance_m | Minimum object distance in meters | numeric | Closest distance at which the lens can achieve focus. Units: m. |
| mod_magnification | Optical magnification at the minimum object distance | numeric | Dimensionless ratio. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M30.5×0.5". Use `ILIKE` for matching. |
| infinity_focus | Whether the lens supports focus at infinity | boolean | TRUE = supports infinity focus; FALSE = does not. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "CS-mount". Use `ILIKE` for filtering. |
| angle_primary_raw | Raw text for the primary FOV angle specification | text | Original source string. Preserved for display. |
| angle_primary_h | Horizontal component of the primary FOV angle | numeric | Units: degrees. |
| angle_primary_v | Vertical component of the primary FOV angle | numeric | Units: degrees. |
| angle_secondary_raw | Raw text for the secondary FOV angle specification | text | FOV at a different sensor size or configuration. |
| angle_secondary_h | Horizontal component of the secondary FOV angle | numeric | Units: degrees. |
| angle_secondary_v | Vertical component of the secondary FOV angle | numeric | Units: degrees. |
| angle_tertiary_raw | Raw text for the tertiary FOV angle specification | text | FOV at a third sensor size or configuration. |
| angle_tertiary_h | Horizontal component of the tertiary FOV angle | numeric | Units: degrees. |
| angle_tertiary_v | Vertical component of the tertiary FOV angle | numeric | Units: degrees. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_mm | Physical length of the lens body in millimeters | numeric | Fixed length (no zoom range). Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `fa_lenses` is the most broadly applicable lens table and shares optical columns (`focus_length_mm`, `f_no_min`, `f_no_max`, `mount_raw`, `weight_g`) with `anti_vibration_lenses`, `autofocus_lenses`, `large_format_lenses`, and line scan lens tables.
* `megapixel_rating` logically links to camera sensor megapixel specifications for system-level compatibility checks.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the focal length, megapixel rating, and weight of all FA lenses?

Reasoning:
- Select identifying and key specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, focus_length_mm, megapixel_rating, weight_g
FROM fa_lenses;
```

---

**2. Megapixel Rating Filter**

Natural Language:
Find all FA lenses rated for 12 megapixels or higher.

Reasoning:
- Filter `megapixel_rating` for high-resolution lenses compatible with modern high-megapixel sensors.

```sql
SELECT model_name, megapixel_rating, focus_length_mm, mount_raw
FROM fa_lenses
WHERE megapixel_rating >= 12;
```

---

**3. Aperture Filter**

Natural Language:
List all FA lenses with a minimum F-number of 1.4 for maximum light collection.

Reasoning:
- Filter `f_no_min` for the widest aperture lenses.

```sql
SELECT model_name, f_no_min, f_no_raw, focus_length_mm, megapixel_rating
FROM fa_lenses
WHERE f_no_min <= 1.4;
```

---

**4. Sensor Size Compatibility**

Natural Language:
Which FA lenses are compatible with a 1-inch sensor?

Reasoning:
- Filter `sensor_size_raw` using `ILIKE` to match 1-inch sensor designation.

```sql
SELECT model_name, sensor_size_raw, focus_length_mm, megapixel_rating
FROM fa_lenses
WHERE sensor_size_raw ILIKE '%1 inch%'
   OR sensor_size_raw ILIKE '%1"% ';
```

---

**5. Distortion Filter**

Natural Language:
Find all FA lenses with TV distortion less than 0.5%.

Reasoning:
- Use `ABS()` to handle signed distortion values.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, focus_length_mm
FROM fa_lenses
WHERE ABS(tv_distortion_percent) < 0.5;
```

---

**6. Infinity Focus Filter**

Natural Language:
Which FA lenses support infinity focus?

Reasoning:
- Filter `infinity_focus` boolean for TRUE.

```sql
SELECT model_name, focus_length_mm, mount_raw, infinity_focus
FROM fa_lenses
WHERE infinity_focus = TRUE;
```

---

**7. FOV Angle Filter**

Natural Language:
List FA lenses with a primary horizontal field of view angle greater than 45 degrees.

Reasoning:
- Filter `angle_primary_h` for wide-angle lenses.

```sql
SELECT model_name, angle_primary_h, angle_primary_v, focus_length_mm
FROM fa_lenses
WHERE angle_primary_h > 45;
```

---

**8. Combined Megapixel and Mount Filter**

Natural Language:
Which FA lenses are rated for at least 20 megapixels and use a C-mount?

Reasoning:
- Combine `megapixel_rating` and `mount_raw` filters for high-resolution C-mount lenses.

```sql
SELECT model_name, megapixel_rating, mount_raw, focus_length_mm
FROM fa_lenses
WHERE megapixel_rating >= 20
  AND mount_raw ILIKE '%C%';
```

---

## Notes

- **Primary Key:** `model_name`
- `megapixel_rating` is an integer representing the maximum sensor resolution the lens can resolve without being the bottleneck; always match or exceed the camera sensor's megapixel count.
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel); use `ABS()` for magnitude-only comparisons. `tv_distortion_operator` gives the inequality context.
- `size_length_mm` is a single fixed value (not a min/max range), reflecting that FA lenses have a fixed body length.
- `infinity_focus = TRUE` is required for applications with variable or very long working distances.
- Three FOV angle column sets (`angle_primary_*`, `angle_secondary_*`, `angle_tertiary_*`) accommodate multiple sensor size configurations.
- All `*_raw` and `mount_raw` fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "FA lens", "factory automation lens", "machine vision lens", "fixed focal length lens", "area scan lens", or "industrial inspection lens".

---
