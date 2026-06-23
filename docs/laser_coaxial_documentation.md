# Table: laser_coaxial_lenses

## Purpose

Stores specifications for **laser coaxial lenses** — specialized optical lenses designed for use with laser light sources in coaxial (on-axis) illumination configurations. Unlike standard broadband machine vision lenses, laser coaxial lenses are optimized for a specific laser wavelength (e.g., 532 nm green, 650 nm red, 850 nm NIR), featuring anti-reflection coatings tuned to that wavelength and optical designs that minimize chromatic artifacts irrelevant in monochromatic laser imaging. These lenses are used in laser triangulation, laser profilometry, structured light scanning, laser speckle inspection, and semiconductor wafer inspection systems where coherent, single-wavelength illumination is integral to the measurement principle.

This table supports engineering lookups for selecting laser coaxial lenses by focal length, sensor size, distortion, field of view angle, filter thread, mount type, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. Longer focal length = narrower FOV and greater working distance. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. In the source price list this is the base USD price × markup × the live USD→INR dollar rate (~95.5). |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel distortion; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M37×0.75". Relevant for attaching laser bandpass or ND filters. Use `ILIKE` for matching. |
| angle_raw | Raw text describing the field of view angle | text | Original source string. Preserved for display. |
| angle_degrees | Field of view angle in degrees | numeric | Total angular FOV. Units: degrees. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_mm | Physical length of the lens body in millimeters | numeric | Fixed length (no zoom range). Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `laser_coaxial_lenses` ↔ `fa_lenses`, `anti_vibration_lenses`, `spectral_lenses`: shares common optical columns (`focus_length_mm`, `tv_distortion_percent`, `mount_raw`, `sensor_size_raw`) for cross-family comparisons.
* `filter_thread_raw` is particularly significant in this table: laser applications frequently require bandpass filters at the laser wavelength mounted on the lens — the filter thread determines filter compatibility.
* `spectral_lenses` is the closest architectural relative, both being wavelength-specific lens families.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all laser coaxial lenses with their focal length, FOV angle, and physical dimensions.

Reasoning:
- Select identifying and key specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, focus_length_mm, angle_degrees, size_diameter_mm, size_length_mm
FROM laser_coaxial_lenses;
```

---

**2. Focal Length Filter**

Natural Language:
Find all laser coaxial lenses with a focal length of 50 mm or longer.

Reasoning:
- Filter `focus_length_mm` for longer focal length lenses with narrower FOV and greater working distance.

```sql
SELECT model_name, focus_length_mm, angle_degrees, mount_raw
FROM laser_coaxial_lenses
WHERE focus_length_mm >= 50;
```

---

**3. FOV Angle Filter**

Natural Language:
Which laser coaxial lenses have a field of view angle greater than 20 degrees?

Reasoning:
- Filter `angle_degrees` for wider-angle lenses covering larger target areas.

```sql
SELECT model_name, angle_degrees, angle_raw, focus_length_mm
FROM laser_coaxial_lenses
WHERE angle_degrees > 20;
```

---

**4. Distortion Filter**

Natural Language:
Find all laser coaxial lenses with TV distortion below 1%.

Reasoning:
- Use `ABS()` to handle both barrel (negative) and pincushion (positive) distortion values.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, focus_length_mm
FROM laser_coaxial_lenses
WHERE ABS(tv_distortion_percent) < 1;
```

---

**5. Mount Compatibility Filter**

Natural Language:
Which laser coaxial lenses use a C-mount?

Reasoning:
- Filter `mount_raw` using `ILIKE` for C-mount lenses.

```sql
SELECT model_name, mount_raw, focus_length_mm, filter_thread_raw
FROM laser_coaxial_lenses
WHERE mount_raw ILIKE '%C%';
```

---

**6. Filter Thread Lookup**

Natural Language:
List all laser coaxial lenses with an M37 filter thread for bandpass filter attachment.

Reasoning:
- Filter `filter_thread_raw` using `ILIKE` for M37 thread compatibility.

```sql
SELECT model_name, filter_thread_raw, focus_length_mm, mount_raw
FROM laser_coaxial_lenses
WHERE filter_thread_raw ILIKE '%M37%';
```

---

**7. Compact Size Filter**

Natural Language:
Find laser coaxial lenses with a body length of 50 mm or less for space-constrained installations.

Reasoning:
- Filter `size_length_mm` for physically compact lenses.

```sql
SELECT model_name, size_length_mm, size_diameter_mm, focus_length_mm
FROM laser_coaxial_lenses
WHERE size_length_mm <= 50;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel); always use `ABS()` for magnitude-only comparisons. `tv_distortion_operator` provides the inequality context.
- `filter_thread_raw` is especially important for this lens family: laser imaging systems commonly require bandpass filters to isolate the laser wavelength and suppress ambient light — verify filter thread compatibility before specifying a filter.
- `angle_degrees` is a single total FOV value (not split into horizontal/vertical) — contrast with multi-angle column sets in other lens tables.
- `size_length_mm` is a fixed single value, reflecting the non-zoom, fixed-body design of these lenses.
- `sensor_size_raw` and `mount_raw` are free-text; always use `ILIKE` with `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "laser lens", "laser coaxial", "laser illumination lens", "coherent light lens", "laser profilometry lens", "laser triangulation lens", or "single wavelength lens".

---
