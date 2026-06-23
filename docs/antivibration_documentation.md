# Table: anti_vibration_lenses

## Purpose

Stores specifications for **anti-vibration lenses** — a specialized class of machine vision lenses equipped with optical image stabilization mechanisms designed to compensate for camera shake, mechanical vibration, or platform motion during image acquisition. These lenses are used in industrial inspection systems mounted on moving platforms, robotic arms, conveyor-side installations, and environments subject to floor vibration or structural resonance. Anti-vibration lenses maintain image sharpness where conventional lenses would produce motion blur.

This table supports engineering lookups for selecting lenses by focal length, aperture, working distance range, field of view angles, sensor size compatibility, physical dimensions, and relative illuminance characteristics. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Longer focal length = narrower FOV and greater working distance. Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. In the source price list this is the base USD price × markup × the live USD→INR dollar rate (~95.5). |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | Original source string (e.g., "1/1.8 inch", "2/3 inch"). Use `ILIKE` for filtering. |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F2.8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤", "=". Used to interpret the distortion specification. |
| tv_distortion_percent | TV distortion magnitude expressed as a percentage | numeric | Values near 0 = minimal distortion. Negative = barrel; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| mod_raw | Raw text for the Minimum Object Distance specification | text | Original source string. Preserved for display. |
| mod_distance_m | Minimum object distance in meters | numeric | Closest distance at which the lens can achieve focus. Units: m. |
| mod_magnification | Optical magnification at the minimum object distance | numeric | Dimensionless ratio. Indicates reproduction scale at closest focus. |
| wd_raw | Raw text representation of the working distance range | text | Original source string. Preserved for display. |
| wd_min_mm | Minimum working distance in millimeters | numeric | Closest operational distance from lens front to target. Units: mm. |
| wd_max_mm | Maximum working distance in millimeters | numeric | Farthest operational distance from lens front to target. Units: mm. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M55×0.75". Use `ILIKE` for matching. |
| relative_illuminance_operator | Comparison operator for relative illuminance value | text | E.g., "≥", ">". Used to interpret the illuminance specification. |
| relative_illuminance_percent | Relative illuminance at the image periphery as a percentage of the center | numeric | Higher value = more uniform illumination across the frame. |
| infinity_focus | Whether the lens supports focus at infinity | boolean | TRUE = supports infinity focus; FALSE = does not. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| angle_primary_raw | Raw text for the primary field of view angle specification | text | Original source string. Preserved for display. |
| angle_primary_h | Horizontal component of the primary FOV angle | numeric | Units: degrees. |
| angle_primary_v | Vertical component of the primary FOV angle | numeric | Units: degrees. |
| angle_secondary_raw | Raw text for the secondary field of view angle specification | text | Represents FOV at a different sensor size or configuration. |
| angle_secondary_h | Horizontal component of the secondary FOV angle | numeric | Units: degrees. |
| angle_secondary_v | Vertical component of the secondary FOV angle | numeric | Units: degrees. |
| angle_tertiary_raw | Raw text for the tertiary field of view angle specification | text | Represents FOV at a third sensor size or configuration. |
| angle_tertiary_h | Horizontal component of the tertiary FOV angle | numeric | Units: degrees. |
| angle_tertiary_v | Vertical component of the tertiary FOV angle | numeric | Units: degrees. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Used for housing and fixture compatibility checks. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Minimum length, e.g., at shortest zoom or focus position. Units: mm. |
| size_length_max_mm | Maximum physical length of the lens body in millimeters | numeric | Maximum length, e.g., at longest zoom or focus extension. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress and robotic integration. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `anti_vibration_lenses` shares common optical specification columns (`focus_length_mm`, `f_no_min`, `f_no_max`, `wd_min_mm`, `wd_max_mm`, `mount_raw`, `weight_g`) with `fa_lenses`, `autofocus_lenses`, `large_format_lenses`, and other lens family tables.
* Cross-table comparisons can be made by focal length, mount type, and sensor size when evaluating alternatives across lens families.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the focal length, working distance range, and weight of all anti-vibration lenses?

Reasoning:
- Select identifying and key specification columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, focus_length_mm, wd_min_mm, wd_max_mm, weight_g
FROM anti_vibration_lenses;
```

---

**2. Aperture Filter**

Natural Language:
Find all anti-vibration lenses with a minimum F-number of 2.8 or lower (fast aperture lenses).

Reasoning:
- Filter `f_no_min` for wide-aperture lenses suitable for low-light or high-speed capture.

```sql
SELECT model_name, f_no_min, f_no_raw, focus_length_mm
FROM anti_vibration_lenses
WHERE f_no_min <= 2.8;
```

---

**3. Working Distance Range Filter**

Natural Language:
Which anti-vibration lenses support a working distance of at least 500 mm?

Reasoning:
- Filter `wd_max_mm` to find lenses that can operate at long distances.

```sql
SELECT model_name, wd_min_mm, wd_max_mm, focus_length_mm
FROM anti_vibration_lenses
WHERE wd_max_mm >= 500;
```

---

**4. Distortion Filter**

Natural Language:
List all anti-vibration lenses with TV distortion below 1%.

Reasoning:
- Use `ABS()` on `tv_distortion_percent` to handle both barrel and pincushion distortion.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator
FROM anti_vibration_lenses
WHERE ABS(tv_distortion_percent) < 1;
```

---

**5. Infinity Focus Support**

Natural Language:
Which anti-vibration lenses support infinity focus?

Reasoning:
- Filter `infinity_focus` boolean for TRUE values.

```sql
SELECT model_name, focus_length_mm, mount_raw, infinity_focus
FROM anti_vibration_lenses
WHERE infinity_focus = TRUE;
```

---

**6. Relative Illuminance Filter**

Natural Language:
Find anti-vibration lenses with relative illuminance of 70% or higher for more uniform image brightness.

Reasoning:
- Filter `relative_illuminance_percent` for lenses with high peripheral brightness uniformity.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator, focus_length_mm
FROM anti_vibration_lenses
WHERE relative_illuminance_percent >= 70;
```

---

**7. Mount and FOV Compatibility**

Natural Language:
List all anti-vibration lenses with a C-mount and a horizontal FOV angle greater than 30 degrees.

Reasoning:
- Filter `mount_raw` for C-mount and `angle_primary_h` for wide field of view.

```sql
SELECT model_name, mount_raw, angle_primary_h, angle_primary_v, focus_length_mm
FROM anti_vibration_lenses
WHERE mount_raw ILIKE '%C%'
  AND angle_primary_h > 30;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Always use `ABS()` for magnitude-only comparisons.
- `tv_distortion_operator` and `relative_illuminance_operator` provide the inequality context for the associated numeric value (e.g., "≤ 1%" means the distortion is at most 1%).
- `wd_min_mm` and `wd_max_mm` define the usable working distance range; filter on `wd_max_mm` for long-range applications and `wd_min_mm` for close-range setups.
- Three sets of FOV angle columns (`angle_primary_*`, `angle_secondary_*`, `angle_tertiary_*`) accommodate multiple sensor size configurations for the same lens.
- `mount_raw`, `sensor_size_raw`, and `filter_thread_raw` are free-text fields; always use `ILIKE` with `%` wildcards.
- `size_length_min_mm` and `size_length_max_mm` represent the physical length range of the lens body across its adjustment range.
- This table is optimized for RAG chunk retrieval when queries mention "anti-vibration", "image stabilization", "vibration compensation", "shake reduction", or "stabilized lens".

---
