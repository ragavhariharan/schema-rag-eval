# Table: large_format_lenses

## Purpose

Stores specifications for **large format lenses** — fixed-focus, high-resolution machine vision lenses engineered for image sensors with large diagonal dimensions (typically greater than 1 inch), including APS-C, full-frame, and specialized industrial large-format sensors. These lenses are used in applications requiring wide-area coverage with high resolution — such as large panel display inspection, solar cell inspection, automotive body inspection, aerial and overhead imaging, and high-megapixel multi-camera systems where conventional C-mount FA lenses cannot cover the sensor's image circle.

This table supports engineering lookups for selecting lenses by megapixel rating, focal length, aperture, maximum image size, magnification range, field of view, distortion, relative illuminance, physical dimensions, and mount compatibility. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| megapixel_rating | Optical resolving power rating of the lens in megapixels | integer | Maximum camera sensor resolution the lens can support without being the resolving bottleneck. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string (e.g., "1.1 inch", "43.3 mm"). Preserved for display. |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed dimension for filtering. Units: mm or inches depending on source context. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel distortion; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| fov_raw | Raw text describing the field of view | text | Original source string. Preserved for display. |
| fov_degrees | Field of view in degrees | numeric | Angular FOV. Units: degrees. |
| fov_mm | Field of view expressed as a linear dimension in millimeters | numeric | Linear FOV at the working distance. Units: mm. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string. Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. Smaller = wider coverage. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. Larger = more zoomed-in coverage. |
| standard_magnification | Standard or nominal magnification label for this lens | text | May include "×" suffix or descriptive labels. Use `ILIKE` for matching. |
| wd_mm | Working distance from lens front element to object surface | numeric | Fixed working distance value. Units: mm. |
| o_i | Object-to-image distance ratio or total conjugate distance | numeric | Optical path length from object to image plane. Used in lens-to-camera alignment. |
| flange_distance | Distance from camera mounting flange to image sensor plane | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "F-mount", "M72", "PF-mount". Use `ILIKE` for filtering. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M95×1.0". Use `ILIKE` for matching. |
| relative_illuminance_operator | Comparison operator for relative illuminance value | text | E.g., "≥", ">". Provides inequality context for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at the image periphery as a percentage of the center | numeric | Higher value = more uniform illumination across the large image circle. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Units: mm. |
| size_length_max_mm | Maximum physical length of the lens body in millimeters | numeric | Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `large_format_lenses` ↔ `large_format_autofocus_lenses`: static and motorized variants of the same large-format lens family. Shares `max_image_size_value`, `focus_length_mm`, `magnification_min`, `magnification_max`, `flange_distance`, and `mount_raw`.
* `megapixel_rating` logically links to camera sensor megapixel specifications for system-level compatibility checks, similar to `fa_lenses.megapixel_rating`.
* `o_i` (object-to-image distance) is shared with `coaxial_illumination_line_scan_lens` for total conjugate distance calculations.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all large format lenses with their megapixel rating, focal length, maximum image size, and weight.

Reasoning:
- Select identifying and key specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, megapixel_rating, focus_length_mm, max_image_size_value, weight_g
FROM large_format_lenses;
```

---

**2. Sensor Size Filter**

Natural Language:
Which large format lenses support a maximum image size of at least 43 mm?

Reasoning:
- Filter `max_image_size_value` for lenses covering large sensor formats such as full-frame or APS-C.

```sql
SELECT model_name, max_image_size_value, max_image_size_raw, focus_length_mm, megapixel_rating
FROM large_format_lenses
WHERE max_image_size_value >= 43;
```

---

**3. Megapixel Rating Filter**

Natural Language:
Find all large format lenses rated for 25 megapixels or higher.

Reasoning:
- Filter `megapixel_rating` for lenses suitable for high-resolution sensors.

```sql
SELECT model_name, megapixel_rating, focus_length_mm, max_image_size_value, mount_raw
FROM large_format_lenses
WHERE megapixel_rating >= 25;
```

---

**4. Aperture Filter**

Natural Language:
List all large format lenses with a minimum F-number of 2.8 or lower.

Reasoning:
- Filter `f_no_min` for wide-aperture lenses with more light-gathering capability.

```sql
SELECT model_name, f_no_min, f_no_raw, focus_length_mm, megapixel_rating
FROM large_format_lenses
WHERE f_no_min <= 2.8;
```

---

**5. Relative Illuminance Filter**

Natural Language:
Which large format lenses have a relative illuminance of 75% or higher at the image periphery?

Reasoning:
- Filter `relative_illuminance_percent` for lenses with uniform brightness across the large image circle.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator, focus_length_mm
FROM large_format_lenses
WHERE relative_illuminance_percent >= 75;
```

---

**6. Distortion Filter**

Natural Language:
Find large format lenses with TV distortion below 0.5%.

Reasoning:
- Use `ABS()` to handle signed distortion values for both barrel and pincushion types.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, focus_length_mm
FROM large_format_lenses
WHERE ABS(tv_distortion_percent) < 0.5;
```

---

**7. Magnification and FOV Filter**

Natural Language:
Which large format lenses support a minimum magnification of 0.05× or lower (very wide coverage)?

Reasoning:
- Filter `magnification_min` for lenses capable of imaging very large objects.

```sql
SELECT model_name, magnification_min, magnification_max, fov_mm, focus_length_mm
FROM large_format_lenses
WHERE magnification_min <= 0.05;
```

---

**8. Mount and Megapixel Combined Filter**

Natural Language:
List large format lenses with an F-mount and a megapixel rating of at least 20.

Reasoning:
- Combine `mount_raw` and `megapixel_rating` filters for F-mount high-resolution systems.

```sql
SELECT model_name, mount_raw, megapixel_rating, focus_length_mm, max_image_size_value
FROM large_format_lenses
WHERE mount_raw ILIKE '%F%'
  AND megapixel_rating >= 20;
```

---

## Notes

- **Primary Key:** `model_name`
- `megapixel_rating` is an integer; always match or exceed the camera sensor's megapixel count to avoid the lens being the resolving bottleneck.
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel); use `ABS()` for magnitude-only comparisons. `tv_distortion_operator` provides the inequality context.
- `relative_illuminance_operator` provides the inequality context for `relative_illuminance_percent` (e.g., "≥ 70%" means periphery brightness is at least 70% of center brightness).
- `wd_mm` is a fixed value for these lenses; contrast with `autofocus_lenses` tables where working distance may be variable.
- `fov_mm` provides the linear field of view at the working distance, while `fov_degrees` gives the angular equivalent — use whichever matches the application requirement.
- `o_i` is the object-to-image (total conjugate) distance; use it for full optical path layout calculations.
- `flange_distance` is the camera-side optical distance; distinct from `wd_mm` (object-side clearance).
- `size_length_min_mm` and `size_length_max_mm` represent the physical body length range.
- All `*_raw` and `mount_raw` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "large format lens", "large sensor lens", "full frame lens", "APS-C lens", "large image circle", "big format machine vision", "F-mount industrial lens", or "high megapixel machine vision lens".

---
