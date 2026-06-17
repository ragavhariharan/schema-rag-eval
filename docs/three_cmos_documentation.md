# Table: three_cmos_lenses

## Purpose

Stores specifications for **3CMOS (three-CMOS-sensor) lenses** — lenses engineered for prism-based three-sensor camera systems (commonly used in high-end broadcast, medical imaging, and high-fidelity color-separation industrial imaging) where a single lens forms an image that is split by a trichroic prism onto three separate CMOS sensors (typically for R/G/B channel separation). These lenses require precise back focal distance, color correction, and image-side resolution to maintain registration and sharpness across all three sensors.

This table supports engineering lookups for selecting lenses by focal length, aperture, magnification range, working distance, flange distance, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| focus_length_mm | Focal length of the lens measured in millimeters | numeric | A longer focal length typically yields narrower field of view and greater working distance. Units: mm. |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string, may include units or format labels (e.g., "1.1 inch", "43.3 mm"). |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed numeric dimension for filtering. Units inferred from raw column context (typically mm or inches). |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F2.8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. Used in low-light or high-speed applications. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤", "=". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Measures geometric distortion of the lens. Lower absolute value = less distortion. Negative values indicate barrel distortion; positive values indicate pincushion distortion. |
| relative_illuminance_operator | Comparison operator associated with the relative illuminance value | text | E.g., "≥", ">". Used to interpret whether `relative_illuminance_percent` is a minimum bound or exact value. |
| relative_illuminance_percent | Relative illuminance at the edge of the image, expressed as a percentage of center illuminance | numeric | Higher values indicate more uniform brightness across the image circle — critical for matching exposure across all three CMOS sensors. |
| image_side_resolution_raw | Raw text representation of the image-side resolving power | text | Original source string, may include units (e.g., "3.45 μm"). |
| image_side_resolution_um | Image-side resolution expressed in micrometers | numeric | Indicates the finest resolvable detail at the image plane; should be matched to sensor pixel pitch. Units: μm. |
| fov_raw | Raw text representation of the field of view | text | Original source string. May describe angular or linear FOV. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string (e.g., "0.1× – 1.0×"). |
| magnification_min | Minimum optical magnification ratio supported | numeric | Dimensionless ratio. Smaller values = wider coverage. |
| magnification_max | Maximum optical magnification ratio supported | numeric | Dimensionless ratio. Larger values = more zoomed-in coverage. |
| wd_raw | Raw text representation of the working distance range | text | Original source string, may describe a fixed value or range (e.g., "0.3 – 1.5 m"). |
| wd_min_m | Minimum working distance in meters | numeric | Closest distance between lens front element and target. Units: m. |
| wd_max_m | Maximum working distance in meters | numeric | Farthest usable distance between lens front element and target. Units: m. |
| flange_distance | Distance from the camera mounting flange to the image sensor plane, measured in millimeters | numeric | Used to confirm physical compatibility with the prism block and camera body. Units: mm. Critical for 3CMOS systems due to the added optical path length of the prism. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount, custom prism mount) | text | Determines mechanical and optical compatibility with the 3CMOS camera body. |
| filter_thread_raw | Raw text representation of the front filter thread size | text | Original source string (e.g., "M52 x 0.75"). Used for attaching filters or hoods. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string, may include diameter and a length range (e.g., "Ø60 x 75 – 95 mm"). |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_min_mm | Minimum overall length of the lens body in millimeters | numeric | Applicable for lenses with adjustable focus/zoom affecting physical length. Units: mm. |
| size_length_max_mm | Maximum overall length of the lens body in millimeters | numeric | Applicable for lenses with adjustable focus/zoom affecting physical length. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `three_cmos_lenses` shares common optical specification columns (`focus_length_mm`, `f_no_min`, `f_no_max`, `tv_distortion_percent`, `relative_illuminance_percent`, `magnification_min`, `magnification_max`, `flange_distance`, `mount_raw`) with other lens tables such as `m12_mount_lenses` and `zoom_lenses`.
* Lenses in this table are specifically designed for prism-based three-sensor color-separation cameras and should be cross-checked against `flange_distance` requirements unique to 3CMOS camera bodies.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the focal length, working distance, and flange distance of all 3CMOS lenses?

```sql
SELECT model_name, focus_length_mm, wd_raw, flange_distance
FROM three_cmos_lenses;
```

---

**2. Attribute Filtering**

Natural Language:
Find all 3CMOS lenses with a minimum F-number of 2.8 or lower (i.e., fast aperture lenses).

```sql
SELECT model_name, f_no_min, f_no_raw
FROM three_cmos_lenses
WHERE f_no_min <= 2.8;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 3CMOS lenses support a maximum image size of at least 43 mm and use a C-mount?

```sql
SELECT model_name, max_image_size_value, mount_raw
FROM three_cmos_lenses
WHERE max_image_size_value >= 43
  AND mount_raw ILIKE '%C%';
```

---

**4. Working Distance Search**

Natural Language:
List all 3CMOS lenses with a maximum working distance greater than 1 meter.

```sql
SELECT model_name, wd_min_m, wd_max_m, focus_length_mm
FROM three_cmos_lenses
WHERE wd_max_m > 1;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What does image-side resolution look like across 3CMOS lenses — which lenses resolve down to 3.45 microns or finer, suitable for matching a 3.45μm pixel pitch sensor?

Reasoning:
- `image_side_resolution_um` stores the resolving power at the image plane.
- Finer (smaller) resolution values indicate the lens can resolve detail matching smaller pixel pitches without becoming the bottleneck.

```sql
SELECT model_name, image_side_resolution_um
FROM three_cmos_lenses
WHERE image_side_resolution_um <= 3.45;
```

---

**6. Mechanical Fit Search**

Natural Language:
Find all 3CMOS lenses with a body diameter under 70mm, suitable for compact camera housings.

```sql
SELECT model_name, size_diameter_mm, size_length_min_mm, size_length_max_mm
FROM three_cmos_lenses
WHERE size_diameter_mm < 70;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `relative_illuminance_percent` should be interpreted alongside `relative_illuminance_operator` — uniform illuminance across the image circle is especially critical in 3CMOS systems to avoid color shading differences between sensors.
- `fov_raw`, `magnification_raw`, `wd_raw`, `filter_thread_raw`, and `size_raw` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "Prism mount").
- `flange_distance` is a critical compatibility parameter for 3CMOS systems because the trichroic prism block adds significant back focal distance compared to single-sensor cameras.
- `image_side_resolution_um` should generally be compared to (and ideally smaller than or equal to) the target sensor's pixel pitch for proper resolution matching.
- This table is optimized for RAG chunk retrieval when queries mention "3CMOS", "three CMOS", "prism camera", "trichroic", or "color separation lens".

---
