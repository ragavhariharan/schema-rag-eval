# Table: m12_mount_lenses

## Purpose

Stores specifications for **M12 mount lenses** — compact, lightweight lenses using the M12 (12mm diameter threaded) mount standard, commonly found in small-form-factor machine vision cameras, embedded vision systems, robotics, drones, and IoT/edge imaging devices. M12 lenses are favored where space and weight constraints are critical, and where moderate resolution sensors (matched to specific megapixel ratings) are used.

This table supports engineering lookups for selecting lenses by megapixel rating, focal length, aperture, field of view (primary and secondary angle), mechanical dimensions, and total track length (TTL). It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| megapixel_rating | Maximum sensor resolution (in megapixels) the lens is designed to support | integer | Higher megapixel rating implies the lens can resolve finer detail without becoming the resolution bottleneck. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. In the source price list this is the base USD price × markup × the live USD→INR dollar rate (~95.5). |
| focus_length_mm | Focal length of the lens measured in millimeters | numeric | A longer focal length typically yields narrower field of view and greater working distance. Units: mm. |
| sensor_size_raw | Raw text representation of the compatible sensor size | text | Original source string, may include formats like "1/2.3 inch" or "1/1.8\"". |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F1.8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. Used in low-light applications. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤", "=". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Measures geometric distortion of the lens. Lower absolute value = less distortion. Negative values indicate barrel distortion; positive values indicate pincushion distortion. |
| relative_illuminance_operator | Comparison operator associated with the relative illuminance value | text | E.g., "≥", ">". Used to interpret whether `relative_illuminance_percent` is a minimum bound or exact value. |
| relative_illuminance_percent | Relative illuminance at the edge of the image, expressed as a percentage of center illuminance | numeric | Higher values indicate more uniform brightness across the image circle. |
| mod_raw | Raw text representation of the minimum object distance | text | Original source string, may include units (e.g., "0.1 m"). |
| mod_distance_m | Minimum object distance (closest focusing distance) in meters | numeric | Defines the closest the lens can focus on a target. Units: m. |
| mod_magnification | Optical magnification at minimum object distance | numeric | Dimensionless ratio describing magnification achieved at closest focus. |
| ttl_raw | Raw text representation of the total track length range | text | Original source string, may describe a fixed value or range (e.g., "20.5 – 22.0 mm"). |
| ttl_min_mm | Minimum total track length (lens mount flange to image plane along optical axis) in millimeters | numeric | Used for mechanical clearance and back focal distance calculations. Units: mm. |
| ttl_max_mm | Maximum total track length in millimeters | numeric | Applicable for lenses with adjustable focus affecting physical length. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | Expected to be "M12" or variants thereof, but preserved as sourced for compatibility checks. |
| angle_primary_raw | Raw text representation of the primary (typically diagonal or horizontal) field of view angle | text | Original source string, may include units (e.g., "78.5°"). |
| angle_primary_h | Primary horizontal field of view angle in degrees | numeric | Used for FOV calculations at a given working distance. Units: degrees. |
| angle_primary_v | Primary vertical field of view angle in degrees | numeric | Used for FOV calculations at a given working distance. Units: degrees. |
| angle_secondary_raw | Raw text representation of the secondary field of view angle (e.g., for an alternate sensor format) | text | Original source string. Some lenses report angles for multiple sensor sizes. |
| angle_secondary_h | Secondary horizontal field of view angle in degrees | numeric | Applies when a secondary sensor size/format is specified. Units: degrees. |
| angle_secondary_v | Secondary vertical field of view angle in degrees | numeric | Applies when a secondary sensor size/format is specified. Units: degrees. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string, may include diameter and length combined (e.g., "Ø17 x 22.5 mm"). |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress, drone/robotics payload, and gimbal balance considerations. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `m12_mount_lenses` shares common optical specification columns (`focus_length_mm`, `f_no_min`, `f_no_max`, `tv_distortion_percent`, `relative_illuminance_percent`, `mount_raw`, `weight_g`) with other lens tables such as `three_cmos_lenses` and `zoom_lenses`.
* Lenses in this table can be cross-referenced against camera modules requiring M12-threaded optics, typically embedded or board-level cameras.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the focal length, F-number range, and weight of all M12 mount lenses?

```sql
SELECT model_name, focus_length_mm, f_no_raw, weight_g
FROM m12_mount_lenses;
```

---

**2. Attribute Filtering**

Natural Language:
Find all M12 mount lenses compatible with a 5 megapixel sensor or higher.

```sql
SELECT model_name, megapixel_rating, focus_length_mm
FROM m12_mount_lenses
WHERE megapixel_rating >= 5;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which M12 mount lenses have a minimum object distance of 0.1 meters or less, suitable for close-range inspection?

```sql
SELECT model_name, mod_distance_m, mod_magnification
FROM m12_mount_lenses
WHERE mod_distance_m <= 0.1;
```

---

**4. Field of View Search**

Natural Language:
List all M12 mount lenses with a primary horizontal field of view greater than 60 degrees.

```sql
SELECT model_name, angle_primary_h, angle_primary_v, focus_length_mm
FROM m12_mount_lenses
WHERE angle_primary_h > 60;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
Which M12 lenses maintain at least 80% relative illuminance at the image edge, ensuring uniform brightness?

Reasoning:
- `relative_illuminance_percent` paired with `relative_illuminance_operator` describes the brightness uniformity bound.
- Use the operator context to confirm whether the stored value is a lower bound (e.g., "≥ 80%").

```sql
SELECT model_name, relative_illuminance_operator, relative_illuminance_percent
FROM m12_mount_lenses
WHERE relative_illuminance_percent >= 80;
```

---

**6. Mechanical Fit Search**

Natural Language:
Find all compact M12 lenses with a diameter under 17mm and weight below 10 grams, suitable for drone-mounted cameras.

```sql
SELECT model_name, size_diameter_mm, weight_g
FROM m12_mount_lenses
WHERE size_diameter_mm < 17
  AND weight_g < 10;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `relative_illuminance_percent` should be interpreted alongside `relative_illuminance_operator` to determine if it represents a guaranteed minimum or a typical value.
- `angle_primary_raw`, `angle_secondary_raw`, `sensor_size_raw`, `mod_raw`, `ttl_raw`, and `size_raw` are text fields preserving original source formatting — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "M12", "M12-mount", "M12 x 0.5").
- `ttl_min_mm` and `ttl_max_mm` may be equal for fixed-focus lenses; a range indicates adjustable focus mechanisms.
- Secondary angle fields (`angle_secondary_h`, `angle_secondary_v`) are often null when only one sensor format is specified by the manufacturer.
- This table is optimized for RAG chunk retrieval when queries mention "M12", "M12 mount", "board lens", "embedded lens", or "miniature lens".

---
