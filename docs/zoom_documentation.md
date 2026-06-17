# Table: zoom_lenses

## Purpose

Stores specifications for **zoom lenses** — machine vision lenses offering variable focal length and/or variable magnification, used in applications requiring flexible field of view adjustment without changing the lens or working distance, such as multi-product inspection lines, semiconductor/electronics inspection, microscopy-adjacent imaging, and telecentric measurement systems. This table covers a broad range of zoom lens types, including motorized and manual zoom/focus mechanisms, telecentric and non-telecentric designs, and lenses with integrated illumination.

This table supports engineering lookups for selecting lenses by zoom type, magnification range, working distance, resolution, numerical aperture, telecentricity, depth of field, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| zoom_type | Classification of the zoom lens design | text | E.g., "motorized zoom", "manual zoom", "fixed zoom step", "continuous zoom". Describes the general category of zoom mechanism. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| illumination_type | Type of integrated illumination, if any | text | E.g., "coaxial", "ring light", "none". Null or "none" indicates no integrated illumination. |
| sensor_size_raw | Raw text representation of the compatible sensor size | text | Original source string, may include formats like "1 inch" or "2/3\"". |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string, may include units or format labels (e.g., "1.1 inch", "43.3 mm"). |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed numeric dimension for filtering. Units inferred from raw column context (typically mm or inches). |
| magnification_raw | Raw text representation of the magnification range | text | Original source string (e.g., "0.5× – 5.0×"). |
| magnification_min | Minimum optical magnification ratio supported | numeric | Dimensionless ratio. Smaller values = wider coverage at the wide end of zoom. |
| magnification_max | Maximum optical magnification ratio supported | numeric | Dimensionless ratio. Larger values = more zoomed-in coverage at the tele end of zoom. |
| wd_raw | Raw text representation of the working distance range | text | Original source string, may describe a fixed value or range (e.g., "60 – 150 mm"). |
| wd_min_mm | Minimum working distance in millimeters | numeric | Closest distance between lens front element and target across the zoom range. Units: mm. |
| wd_max_mm | Maximum working distance in millimeters | numeric | Farthest usable distance between lens front element and target across the zoom range. Units: mm. |
| resolution_raw | Raw text representation of the optical resolution range | text | Original source string, may include units (e.g., "2.0 – 8.0 μm"). |
| resolution_min_um | Minimum (finest) resolvable detail size in micrometers | numeric | Smaller value = finer resolving power, typically at the tele/high-magnification end. Units: μm. |
| resolution_max_um | Maximum (coarsest) resolvable detail size in micrometers | numeric | Larger value = coarser resolving power, typically at the wide/low-magnification end. Units: μm. |
| numerical_aperture_raw | Raw text representation of the numerical aperture range | text | Original source string (e.g., "NA 0.05 – 0.15"). |
| numerical_aperture_min | Minimum numerical aperture value | numeric | Dimensionless. Relates to light-gathering ability and resolving power; lower NA generally corresponds to greater depth of field. |
| numerical_aperture_max | Maximum numerical aperture value | numeric | Dimensionless. Higher NA generally corresponds to finer resolution but shallower depth of field. |
| zoom_method | Mechanism by which zoom (focal length/magnification change) is achieved | text | E.g., "motorized", "manual ring", "electronic". |
| focus_method | Mechanism by which focus is achieved | text | E.g., "motorized", "manual ring", "fixed focus". |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F2.8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. Used in low-light or high-speed applications. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| nd | Neutral density factor, if applicable | numeric | Indicates light attenuation factor for an integrated or optional ND filter element; null if not applicable. |
| telecentricity_raw | Raw text representation of the telecentricity specification | text | Original source string (e.g., "< 0.05°"). Indicates whether the lens is telecentric and to what degree. |
| telecentricity_degrees | Telecentricity error expressed in degrees | numeric | Lower values indicate better telecentricity (more parallel chief rays), important for accurate dimensional measurement applications. Units: degrees. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤", "=". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Measures geometric distortion of the lens. Lower absolute value = less distortion. Negative values indicate barrel distortion; positive values indicate pincushion distortion. |
| relative_illuminance_operator | Comparison operator associated with the relative illuminance value | text | E.g., "≥", ">". Used to interpret whether `relative_illuminance_percent` is a minimum bound or exact value. |
| relative_illuminance_percent | Relative illuminance at the edge of the image, expressed as a percentage of center illuminance | numeric | Higher values indicate more uniform brightness across the image circle. |
| object_resolution_raw | Raw text representation of the object-side resolution | text | Original source string, may include units (e.g., "5 μm"). |
| object_resolution_um | Object-side resolving power in micrometers | numeric | Indicates the finest resolvable detail at the object/target plane, distinct from image-side resolution. Units: μm. |
| dof_raw | Raw text representation of the depth of field range | text | Original source string, may describe a fixed value or range (e.g., "0.5 – 3.0 mm"). |
| dof_min_mm | Minimum depth of field in millimeters | numeric | Typically corresponds to the high-magnification/high-NA end of the zoom range, where DOF is shallowest. Units: mm. |
| dof_max_mm | Maximum depth of field in millimeters | numeric | Typically corresponds to the low-magnification/low-NA end of the zoom range, where DOF is deepest. Units: mm. |
| ttl_mm | Total track length (lens mount flange to image plane along optical axis) in millimeters | numeric | Used for mechanical clearance and back focal distance calculations. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount, M42) | text | Determines mechanical and optical compatibility with camera. |
| filter_thread_raw | Raw text representation of the front filter thread size | text | Original source string (e.g., "M52 x 0.75"). Used for attaching filters or hoods. |
| flange_distance | Distance from the camera mounting flange to the image sensor plane, measured in millimeters | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string, may include diameter and length combined (e.g., "Ø90 x 180 mm"). |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress and robotic integration, especially relevant for motorized zoom lenses which tend to be heavier. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `zoom_lenses` shares common optical specification columns (`f_no_min`, `f_no_max`, `tv_distortion_percent`, `relative_illuminance_percent`, `magnification_min`, `magnification_max`, `mount_raw`, `flange_distance`, `weight_g`) with other lens tables such as `m12_mount_lenses` and `three_cmos_lenses`.
* Lenses with `illumination_type` set to "coaxial" are logically related to `coaxial_illumination_line_scan_lens` and other coaxial illumination lens tables, sharing the on-axis lighting design principle.
* `zoom_method` and `focus_method` jointly describe the lens's adjustment mechanism and can be cross-referenced for automation/integration requirements (e.g., motorized lenses for automated multi-product lines).

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the magnification range, working distance, and weight of all zoom lenses?

```sql
SELECT model_name, magnification_min, magnification_max, wd_raw, weight_g
FROM zoom_lenses;
```

---

**2. Attribute Filtering**

Natural Language:
Find all zoom lenses with motorized zoom and motorized focus, suitable for automated inspection lines.

```sql
SELECT model_name, zoom_method, focus_method
FROM zoom_lenses
WHERE zoom_method ILIKE '%motor%'
  AND focus_method ILIKE '%motor%';
```

---

**3. Compatibility Reasoning**

Natural Language:
Which zoom lenses support a maximum magnification of at least 5x and use a C-mount?

```sql
SELECT model_name, magnification_max, mount_raw
FROM zoom_lenses
WHERE magnification_max >= 5
  AND mount_raw ILIKE '%C%';
```

---

**4. Working Distance Search**

Natural Language:
List all zoom lenses with a minimum working distance greater than 100 mm.

```sql
SELECT model_name, wd_min_mm, wd_max_mm
FROM zoom_lenses
WHERE wd_min_mm > 100;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
Which zoom lenses are telecentric with less than 0.1 degrees of telecentricity error, suitable for precision dimensional measurement?

Reasoning:
- `telecentricity_degrees` stores the telecentricity error; smaller values indicate better parallelism of chief rays.
- A near-zero value is required for accurate edge/dimensional measurement applications.

```sql
SELECT model_name, telecentricity_degrees, numerical_aperture_min, numerical_aperture_max
FROM zoom_lenses
WHERE telecentricity_degrees < 0.1;
```

---

**6. Depth of Field Search**

Natural Language:
Find zoom lenses with a maximum depth of field greater than 2mm, useful for inspecting uneven or 3D surfaces.

```sql
SELECT model_name, dof_min_mm, dof_max_mm, magnification_min, magnification_max
FROM zoom_lenses
WHERE dof_max_mm > 2;
```

---

**7. Illumination-Based Search**

Natural Language:
Which zoom lenses have integrated coaxial illumination?

```sql
SELECT model_name, illumination_type, focus_length_mm
FROM zoom_lenses
WHERE illumination_type ILIKE '%coaxial%';
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `relative_illuminance_percent` should be interpreted alongside `relative_illuminance_operator` to determine if it represents a guaranteed minimum or typical value.
- `sensor_size_raw`, `max_image_size_raw`, `magnification_raw`, `wd_raw`, `resolution_raw`, `numerical_aperture_raw`, `telecentricity_raw`, `object_resolution_raw`, `dof_raw`, `filter_thread_raw`, and `size_raw` are text fields preserving original source formatting — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "F-mount").
- Note that this table does **not** contain a `focus_length_mm` column directly in all cases since zoom lenses operate across a variable focal length range rather than a single fixed value — refer to `magnification_min`/`magnification_max` and `fov`-related raw fields for range-based filtering instead.
- `resolution_min_um`/`resolution_max_um` and `object_resolution_um` are related but distinct: the former describes image-side resolving power across the zoom range, the latter describes object-side resolving power at a specific configuration.
- `nd` (neutral density) is often null for lenses without an integrated ND filter element.
- `dof_min_mm` typically pairs with high magnification/high NA settings, while `dof_max_mm` pairs with low magnification/low NA settings.
- This table is optimized for RAG chunk retrieval when queries mention "zoom lens", "motorized zoom", "telecentric zoom", "variable magnification", or "continuous zoom".

---
