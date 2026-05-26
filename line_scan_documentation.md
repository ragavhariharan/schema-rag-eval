# Lens Schema Documentation
> RAG-ready knowledge base for machine vision lens database tables.
> All tables use `model_name` as the primary key. No foreign key relationships exist across tables.

---

# Table: coaxial_illumination_line_scan_lens

## Purpose

Stores specifications for **coaxial illumination line scan lenses** — a specialized class of industrial machine vision lenses that integrate coaxial (on-axis) illumination directly into the lens body. These lenses are used in high-speed line scan imaging systems for web inspection, flat panel display inspection, PCB quality control, and other continuous-motion inspection applications where uniform, reflection-free illumination is critical.

This table supports engineering lookups for selecting lenses by focal length, aperture, working distance, magnification range, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens measured in millimeters | numeric | A longer focal length typically yields narrower field of view and greater working distance. Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string, may include units or format labels (e.g., "1.1 inch", "43.3 mm"). |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed numeric dimension for filtering. Units inferred from raw column context (typically mm or inches). |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F2.8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. Used in low-light or high-speed applications. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Measures geometric distortion of the lens. Lower absolute value = less distortion. Negative values indicate barrel distortion; positive values indicate pincushion distortion. |
| fov_raw | Raw text representation of the field of view | text | Original source string. May describe angular or linear FOV. |
| magnification_min | Minimum optical magnification ratio supported | numeric | Dimensionless ratio (e.g., 0.1× to 2×). Smaller values = wider coverage. |
| magnification_max | Maximum optical magnification ratio supported | numeric | Dimensionless ratio. Larger values = more zoomed-in coverage. |
| standard_magnification | Standard or nominal magnification value for this lens | text | Text field — may include units like "×" or descriptive labels. |
| wd_mm | Working distance between the lens front element and the object/target surface, measured in millimeters | numeric | Critical for mounting and integration planning. Units: mm. |
| o_i | Object-to-image distance ratio or total conjugate distance | numeric | Represents the optical path length from object to image plane. Used in lens-to-camera alignment. |
| flange_distance | Distance from the camera mounting flange to the image sensor plane, measured in millimeters | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount, M42) | text | Determines mechanical and optical compatibility with camera. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress and robotic integration. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `coaxial_illumination_line_scan_lens` ↔ `line_scan_lens_4k7u`, `line_scan_lens_8k5u`, `line_scan_lens_8k7u`, `line_scan_lens_12k5u`, `line_scan_lens_16k3_5u`, `line_scan_lens_16k5u`, `new_series_line_scan_lens_4k7u`
* All tables share common optical specification columns (`focus_length_mm`, `wd_mm`, `f_no_min`, `f_no_max`, `magnification_min`, `magnification_max`, `mount_raw`, `weight_g`).
* Lenses across these tables serve related line scan camera systems and can be cross-referenced by focal length, mount type, and sensor size compatibility.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the focal length, working distance, and weight of all coaxial illumination line scan lenses?

Reasoning:
- Select the identifying column and the three requested specification columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, focus_length_mm, wd_mm, weight_g
FROM coaxial_illumination_line_scan_lens;
```

---

**2. Attribute Filtering**

Natural Language:
Find all coaxial illumination line scan lenses with a minimum F-number of 2.8 or lower (i.e., fast aperture lenses).

Reasoning:
- Filter on `f_no_min` to find lenses that support wide aperture settings.
- Lower F-number = faster lens = better in low-light or high-speed scenarios.

```sql
SELECT model_name, f_no_min, f_no_raw
FROM coaxial_illumination_line_scan_lens
WHERE f_no_min <= 2.8;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which coaxial illumination line scan lenses support a maximum image size of at least 43 mm and use a C-mount?

Reasoning:
- Filter `max_image_size_value` for large sensor coverage.
- Filter `mount_raw` for C-mount compatibility.

```sql
SELECT model_name, max_image_size_value, mount_raw
FROM coaxial_illumination_line_scan_lens
WHERE max_image_size_value >= 43
  AND mount_raw ILIKE '%C%';
```

---

**4. Working Distance Search**

Natural Language:
List all coaxial illumination line scan lenses with a working distance greater than 100 mm.

Reasoning:
- Filter on `wd_mm` to find lenses suitable for applications requiring clearance between lens and target.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM coaxial_illumination_line_scan_lens
WHERE wd_mm > 100;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What does TV distortion look like across coaxial illumination lenses — are there any lenses with distortion below 0.1%?

Reasoning:
- `tv_distortion_percent` stores TV distortion. Values close to 0 indicate minimal distortion.
- Use `ABS()` to handle both barrel (negative) and pincushion (positive) distortion.

```sql
SELECT model_name, tv_distortion_percent
FROM coaxial_illumination_line_scan_lens
WHERE ABS(tv_distortion_percent) < 0.1;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons.
- `fov_raw` and `standard_magnification` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "C").
- `o_i` refers to the object-to-image distance ratio, a key value in optical conjugate distance calculations.
- `flange_distance` is distinct from working distance (`wd_mm`); it describes the camera-side optical distance.
- This table is optimized for RAG chunk retrieval when queries mention "coaxial", "integrated illumination", "on-axis lighting", or "line scan lens".

---

---

# Table: line_scan_lens_12k5u

## Purpose

Stores specifications for **line scan lenses optimized for 12K resolution sensors with 5 µm pixel pitch**. These lenses are designed for high-resolution continuous-scan industrial imaging systems, including web inspection, solar cell inspection, and printed material quality control. The "12k" in the table name refers to 12,000-pixel sensor resolution and "5u" refers to the 5-micron pixel size.

This table supports engineering lookups for selecting lenses by focal length, working distance, magnification, field of view, aperture, mount type, filter thread, and physical size.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | No explicit primary key constraint in this table per schema (is_nullable: YES); acts as a de facto identifier. |
| focus_length_mm | Focal length of the lens measured in millimeters | numeric | Core optical parameter. Longer focal lengths yield narrower FOV and longer working distances. Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text representation of the maximum sensor coverage supported | text | Original string format. May include inch or mm notation. |
| max_image_size_value | Numeric extracted value of the maximum image size | numeric | Numeric dimension for filtering and compatibility matching. |
| f_no_raw | Raw text of the F-number range (aperture specification) | text | Original source string retained for display purposes. |
| f_no_min | Minimum F-number (maximum aperture) of the lens | numeric | Lower value = larger aperture = more light transmission. |
| f_no_max | Maximum F-number (minimum aperture) of the lens | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for the TV distortion specification (e.g., `<`, `≤`) | text | Used alongside `tv_distortion_percent` to express an inequality specification. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Geometric distortion metric. Lower absolute value = less image shape error. |
| fov_mm | Field of view measured in millimeters | numeric | Linear FOV at the object plane. Directly relates to coverage width on the target surface. Units: mm. |
| magnification_min | Minimum supported optical magnification ratio | numeric | Dimensionless. Smaller = wider coverage. |
| magnification_max | Maximum supported optical magnification ratio | numeric | Dimensionless. Larger = more detailed close-up coverage. |
| standard_magnification | Standard nominal magnification for this lens model | numeric | Single reference magnification value. Numeric type (unlike text in other tables). |
| wd_mm | Working distance from the lens to the target object surface in millimeters | numeric | Critical for fixture and mount design. Units: mm. |
| o_i | Object-to-image distance or total conjugate ratio | numeric | Optical path metric used for lens-camera alignment and system layout. |
| flange_distance | Flange-to-sensor distance on the camera side in millimeters | numeric | Used to verify camera body compatibility. Units: mm. |
| mount_raw | Raw text describing the lens mount type | text | Determines mechanical compatibility with camera (e.g., C-mount, F-mount). |
| filter_thread_raw | Raw text describing the filter thread size and pitch | text | Indicates compatibility with optical filters (e.g., "M55 × 0.75"). |
| relative_illuminance_operator | Comparison operator for the relative illuminance specification | text | Paired with `relative_illuminance_percent` to express a bound (e.g., `≥`). |
| relative_illuminance_percent | Relative illuminance at the edge of the image field, expressed as a percentage of center illuminance | numeric | Higher values indicate more uniform illumination across the field. Units: %. |
| size_raw | Raw text description of the physical lens dimensions | text | Original source string (e.g., "Ø52 × 89.8 mm"). |
| size_diameter_mm | Physical outer diameter of the lens body in millimeters | numeric | Used for space and clearance planning. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Minimum value, suggesting adjustable or range-dependent length. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for vibration tolerance and mounting load. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_12k5u` ↔ `line_scan_lens_8k5u`, `line_scan_lens_16k5u`
* All three tables share a "5u" (5 µm pixel pitch) design target and have nearly identical schema structures (`fov_mm`, `f_no_min`, `f_no_max`, `relative_illuminance_percent`, `filter_thread_raw`).
* Can be cross-referenced to compare lens options across 8K, 12K, and 16K sensor resolutions at the same pixel pitch.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 12K 5µm line scan lenses with their focal length, working distance, and list price.

Reasoning:
- Retrieve the three requested columns plus the identifier.
- No filtering — return all models.

```sql
SELECT model_name, focus_length_mm, wd_mm, list_price
FROM line_scan_lens_12k5u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 12K 5µm lenses with relative illuminance of 60% or greater at the field edge.

Reasoning:
- Filter on `relative_illuminance_percent` to find lenses with uniform illumination.
- Higher relative illuminance = better edge brightness = less vignetting.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator
FROM line_scan_lens_12k5u
WHERE relative_illuminance_percent >= 60;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 12K 5µm lenses have a filter thread and support a maximum image size of at least 60 mm?

Reasoning:
- Filter on `filter_thread_raw` for non-null filter thread availability.
- Filter on `max_image_size_value` for large sensor coverage.

```sql
SELECT model_name, filter_thread_raw, max_image_size_value
FROM line_scan_lens_12k5u
WHERE filter_thread_raw IS NOT NULL
  AND max_image_size_value >= 60;
```

---

**4. Working Distance Search**

Natural Language:
Show all 12K 5µm line scan lenses with a working distance between 100 mm and 300 mm.

Reasoning:
- Use a range filter on `wd_mm` to narrow down lenses that fit within a specific mounting envelope.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_12k5u
WHERE wd_mm BETWEEN 100 AND 300;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What is the "standard magnification" for each 12K 5µm lens, and how does it relate to field of view?

Reasoning:
- `standard_magnification` is a single reference magnification value.
- `fov_mm` is the corresponding field of view at that magnification.
- Retrieving both reveals the relationship between magnification and coverage width.

```sql
SELECT model_name, standard_magnification, fov_mm
FROM line_scan_lens_12k5u
ORDER BY standard_magnification;
```

---

## Notes

- **Primary Key:** `model_name` (no explicit constraint in schema, but serves as de facto identifier)
- `tv_distortion_operator` and `relative_illuminance_operator` are companion columns — always query them together with their `_percent` counterparts.
- `size_length_min_mm` suggests the lens may have a variable or adjustable length; use this as a minimum bound.
- `fov_mm` is a numeric linear field of view — useful for direct comparison with sensor scan width.
- `standard_magnification` is stored as numeric (unlike text in other tables), enabling arithmetic operations.
- RAG retrieval hint: this table is relevant to queries mentioning "12K", "12000 pixel", "5 micron pixel", or "high resolution line scan".

---

---

# Table: line_scan_lens_16k3_5u

## Purpose

Stores specifications for **line scan lenses designed for 16K resolution sensors with 3.5 µm pixel pitch**. These are among the highest-resolution line scan lenses, intended for ultra-fine inspection tasks such as flat panel display inspection, semiconductor wafer inspection, and precision web defect detection where fine spatial detail is required.

This table supports engineering selection by focal length, field of view (in both degrees and millimeters), working distance, magnification, mount type, filter thread, and physical dimensions.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Core optical design parameter. Units: mm. |
| list_price | Catalogue sales price | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of maximum supported sensor/image size | text | Original string format with units. |
| max_image_size_value | Numeric extracted maximum image size value | numeric | Numeric dimension used for filtering. |
| f_no_raw | Raw text of the F-number range | text | Original aperture specification string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = more light. |
| f_no_max | Maximum F-number (smallest aperture) | numeric | Higher = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion (e.g., `<`, `≤`) | text | Paired with `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion value in percent | numeric | Geometric distortion metric. Closer to 0 = less distortion. |
| fov_raw | Raw text field of view specification | text | Original source string. |
| fov_degrees | Field of view expressed in degrees | numeric | Angular FOV measurement. Useful for optical system layout calculations. Units: degrees. |
| fov_mm | Field of view expressed in millimeters | text | Linear FOV at the object plane. Stored as text — may contain range or formatted values. Units: mm. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless ratio. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless ratio. |
| standard_magnification | Standard or nominal magnification for this lens | text | Reference magnification label. Text type — may include formatting. |
| wd_mm | Working distance from lens front to target in millimeters | numeric | Mounting clearance parameter. Units: mm. |
| o_i | Object-to-image distance or total conjugate distance | numeric | Optical system path metric. |
| flange_distance | Lens flange to image sensor distance in millimeters | numeric | Camera-side optical distance. Units: mm. |
| mount_raw | Raw text for camera mount type | text | Mechanical compatibility identifier (e.g., C-mount, F-mount). |
| filter_thread_raw | Raw text for filter thread specification | text | Optical filter compatibility (e.g., thread diameter and pitch). |
| size_raw | Raw text for physical lens dimensions | text | Original string (e.g., "Ø72 × 120 mm"). |
| size_diameter_mm | Physical outer diameter of the lens in millimeters | numeric | Space/clearance dimension. Units: mm. |
| size_length_mm | Physical length of the lens body in millimeters | numeric | Fixed length dimension (not a minimum — this is a single value). Units: mm. |
| weight_g | Weight of the lens in grams | numeric | Mounting load consideration. Units: g. |
| relative_illuminance_operator | Comparison operator for relative illuminance specification | text | Paired with `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at field edge as percentage of center | numeric | Uniformity metric. Higher = less vignetting. Units: %. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_16k3_5u` ↔ `line_scan_lens_16k5u`
* Both serve 16K sensor formats but at different pixel pitches (3.5 µm vs. 5 µm). Cross-table comparison can identify the best lens for a given 16K camera depending on pixel size.
* Also logically related to `line_scan_lens_8k5u` and `line_scan_lens_12k5u` as part of a family of high-resolution line scan lens offerings.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
Show all 16K 3.5µm lenses with their focal length, angular field of view, and price.

Reasoning:
- Select `focus_length_mm`, `fov_degrees`, and `list_price` alongside `model_name`.

```sql
SELECT model_name, focus_length_mm, fov_degrees, list_price
FROM line_scan_lens_16k3_5u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 16K 3.5µm lenses with TV distortion less than 0.05%.

Reasoning:
- Filter on `tv_distortion_percent` with a low threshold for precision inspection applications.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator
FROM line_scan_lens_16k3_5u
WHERE tv_distortion_percent < 0.05;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 16K 3.5µm lenses support sensors larger than 55 mm and have a filter thread available?

Reasoning:
- Filter `max_image_size_value` for large format sensor coverage.
- Filter `filter_thread_raw` for non-null values indicating filter support.

```sql
SELECT model_name, max_image_size_value, filter_thread_raw
FROM line_scan_lens_16k3_5u
WHERE max_image_size_value > 55
  AND filter_thread_raw IS NOT NULL;
```

---

**4. Working Distance Search**

Natural Language:
List all 16K 3.5µm lenses with a working distance of at least 200 mm.

Reasoning:
- Filter on `wd_mm` to find lenses for large-standoff mounting configurations.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_16k3_5u
WHERE wd_mm >= 200;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What is the difference between "fov_degrees" and "fov_mm" — show both for all models.

Reasoning:
- `fov_degrees` is angular field of view; `fov_mm` is linear field of view at the object plane.
- Retrieving both side by side clarifies the relationship.

```sql
SELECT model_name, fov_degrees, fov_mm
FROM line_scan_lens_16k3_5u;
```

---

## Notes

- **Primary Key:** `model_name`
- This table uniquely includes both `fov_degrees` (numeric) and `fov_mm` (text), covering both angular and linear FOV representations.
- `size_length_mm` is a fixed single value (not a min/max range) — distinct from `size_length_min_mm` used in other tables.
- `relative_illuminance_operator` and `tv_distortion_operator` must be interpreted alongside their `_percent` values.
- RAG retrieval hint: relevant to queries mentioning "16K", "3.5 micron", "ultra fine pitch", "high resolution line scan".

---

---

# Table: line_scan_lens_16k5u

## Purpose

Stores specifications for **line scan lenses designed for 16K resolution sensors with 5 µm pixel pitch**. This table covers a higher-resolution variant of the 5 µm pixel pitch lens family, targeting applications such as wide-web inspection, large-format print inspection, and solar panel quality control where both wide coverage and high resolution are needed simultaneously.

This table supports selection by focal length, working distance, field of view (angular and linear), magnification, mount, filter thread, and physical dimensions.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Core optical parameter. Units: mm. |
| list_price | Catalogue price of the lens | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of the maximum supported image/sensor size | text | Original source string with formatting. |
| max_image_size_value | Numeric extracted value of the maximum image size | numeric | Used for filtering by sensor coverage. |
| f_no_raw | Raw text of the F-number (aperture) range | text | Original aperture string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = more light admitted. |
| f_no_max | Maximum F-number (smallest aperture) | numeric | Higher = greater depth of field. |
| tv_distortion_percent | TV distortion in percent | numeric | Geometric distortion metric. Lower absolute value = less distortion. |
| fov_raw | Raw text field of view specification | text | Original source string. |
| fov_degrees | Field of view in degrees (angular) | numeric | Angular coverage. Units: degrees. |
| fov_mm | Field of view in millimeters (linear) at the object plane | text | Stored as text — may contain formatted values. Units: mm. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| standard_magnification | Standard nominal magnification for this lens | text | Text reference value; may include "×" symbol. |
| wd_mm | Working distance from lens front to target in millimeters | numeric | Mount clearance parameter. Units: mm. |
| o_i | Object-to-image distance / total conjugate | numeric | Optical path metric. |
| flange_distance | Camera flange to sensor distance in millimeters | numeric | Camera-side optical compatibility. Units: mm. |
| mount_raw | Raw text of camera mount type | text | Mount compatibility label. |
| filter_thread_raw | Raw text of filter thread size/pitch | text | Filter compatibility specification. |
| size_raw | Raw text of physical lens dimensions | text | Original formatted dimension string. |
| size_diameter_mm | Physical outer diameter of the lens in millimeters | numeric | Clearance/space planning. Units: mm. |
| weight_g | Weight of the lens in grams | numeric | Mounting load parameter. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_16k5u` ↔ `line_scan_lens_16k3_5u`
* Both target 16K sensors but differ in pixel pitch (5 µm vs. 3.5 µm). Can be compared when selecting a lens for a specific 16K camera model.
* `line_scan_lens_16k5u` ↔ `line_scan_lens_8k5u`, `line_scan_lens_12k5u`
* Shares the 5 µm pixel pitch target. Cross-table resolution family comparison is supported.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 16K 5µm line scan lenses with their focal length, field of view in degrees, and weight.

Reasoning:
- Select the four relevant columns for all models.

```sql
SELECT model_name, focus_length_mm, fov_degrees, weight_g
FROM line_scan_lens_16k5u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 16K 5µm lenses with an outer diameter of less than 80 mm for space-constrained installations.

Reasoning:
- Filter on `size_diameter_mm` to find compact lens options.

```sql
SELECT model_name, size_diameter_mm, weight_g
FROM line_scan_lens_16k5u
WHERE size_diameter_mm < 80;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 16K 5µm lenses support F-numbers below 4 and have a maximum image size above 60 mm?

Reasoning:
- Filter `f_no_min` for fast aperture lenses.
- Filter `max_image_size_value` for large sensor coverage.

```sql
SELECT model_name, f_no_min, max_image_size_value
FROM line_scan_lens_16k5u
WHERE f_no_min < 4
  AND max_image_size_value > 60;
```

---

**4. Working Distance Search**

Natural Language:
Show 16K 5µm lenses where working distance is between 150 mm and 400 mm.

Reasoning:
- Range filter on `wd_mm` for mid-range standoff mounting configurations.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_16k5u
WHERE wd_mm BETWEEN 150 AND 400;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What is "flange distance" and how does it compare to working distance for these lenses?

Reasoning:
- `flange_distance` is the camera-side optical distance (lens flange to image sensor).
- `wd_mm` is the object-side distance (lens front to target).
- Showing both reveals the full optical conjugate layout.

```sql
SELECT model_name, wd_mm, flange_distance
FROM line_scan_lens_16k5u;
```

---

## Notes

- **Primary Key:** `model_name`
- This table does NOT have `size_length_mm` or `size_length_min_mm` — only `size_diameter_mm` and `weight_g` represent physical dimensions alongside `size_raw`.
- `tv_distortion_percent` has no companion `_operator` column here — treat the value directly.
- `fov_mm` is text type despite being a millimeter value — use `CAST` or string parsing if numeric operations are needed.
- RAG hint: relevant for "16K 5µm", "wide format line scan", "large sensor line scan lens" queries.

---

---

# Table: line_scan_lens_4k7u

## Purpose

Stores specifications for **line scan lenses designed for 4K resolution sensors with 7 µm pixel pitch**. These lenses are suited for moderate-resolution high-speed inspection tasks such as bottle inspection, label verification, and wood/textile surface defect detection where sensor resolution is lower but pixel size is larger, allowing more light per pixel.

This table supports engineering selection by focal length, aperture, working distance, field of view, magnification, mount, filter thread, and physical dimensions.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length in millimeters | numeric | Core optical parameter. Units: mm. |
| list_price | Catalogue price | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of maximum supported image/sensor size | text | Original string format. |
| max_image_size_value | Numeric extracted maximum image size | numeric | Dimension for sensor compatibility filtering. |
| f_no_raw | Raw text of the F-number range | text | Original aperture specification string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = brighter image. |
| f_no_max | Maximum F-number or limit value | text | Stored as text — may include symbolic notation (e.g., "closed"). Check before casting. |
| tv_distortion_operator | Comparison operator for TV distortion | text | Qualifier for `tv_distortion_percent` (e.g., `<`, `≤`). |
| tv_distortion_percent | TV distortion in percent | numeric | Geometric distortion metric. |
| fov_mm | Field of view in millimeters | text | Linear coverage at the object plane. Text type — may contain formatted values. Units: mm. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| standard_magnification | Standard or nominal magnification reference | text | Text label with magnification value. |
| wd_mm | Working distance from lens to object in millimeters | numeric | Mounting clearance. Units: mm. |
| o_i | Object-to-image distance or total conjugate | numeric | Optical path metric. |
| flange_distance | Camera flange to image sensor distance in millimeters | numeric | Camera compatibility value. Units: mm. |
| mount_raw | Raw text of camera mount type | text | Mount compatibility identifier. |
| filter_thread_raw | Raw text of filter thread specification | text | Optical filter compatibility. |
| relative_illuminance_operator | Comparison operator for relative illuminance | text | Qualifier for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at image field edge as percentage | numeric | Uniformity metric. Higher = less vignetting. Units: %. |
| size_raw | Raw text of physical lens size description | text | Original formatted dimension string. |
| size_diameter_mm | Physical outer diameter in millimeters | numeric | Space/clearance dimension. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens in millimeters | numeric | Minimum bound; lens may be adjustable. Units: mm. |
| weight_g | Physical weight of the lens in grams | numeric | Mounting load. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_4k7u` ↔ `new_series_line_scan_lens_4k7u`
* Both tables target 4K sensors with 7 µm pixel pitch. The `new_series` variant is a newer product generation sharing the same sensor target. Cross-table comparison can identify generational differences in specifications.
* `line_scan_lens_4k7u` ↔ `line_scan_lens_8k7u`
* Both target 7 µm pixel pitch sensors at different resolutions (4K vs. 8K). Useful when selecting between resolution tiers for the same pixel size.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
Show all 4K 7µm line scan lenses with focal length, working distance, and field of view.

Reasoning:
- Select `focus_length_mm`, `wd_mm`, and `fov_mm` for all models.

```sql
SELECT model_name, focus_length_mm, wd_mm, fov_mm
FROM line_scan_lens_4k7u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 4K 7µm lenses with relative illuminance of at least 50%.

Reasoning:
- Filter `relative_illuminance_percent` to find lenses with acceptable field uniformity.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator
FROM line_scan_lens_4k7u
WHERE relative_illuminance_percent >= 50;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 4K 7µm lenses support a sensor image size of 29 mm or larger and have a filter thread?

Reasoning:
- Filter `max_image_size_value` and `filter_thread_raw` for combined compatibility check.

```sql
SELECT model_name, max_image_size_value, filter_thread_raw
FROM line_scan_lens_4k7u
WHERE max_image_size_value >= 29
  AND filter_thread_raw IS NOT NULL;
```

---

**4. Working Distance Search**

Natural Language:
List all 4K 7µm lenses with working distance under 100 mm for close-range inspection.

Reasoning:
- Filter `wd_mm` for short standoff distance requirements.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_4k7u
WHERE wd_mm < 100;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
The spec sheet mentions "f_no_max" — why is it stored as text instead of a number?

Reasoning:
- `f_no_max` is `text` type in this table (unlike other tables where it is `numeric`).
- This may be because some models use symbolic values (e.g., "∞", "closed") rather than a defined number.
- Querying with a cast is necessary for numeric comparisons.

```sql
SELECT model_name, f_no_raw, f_no_min, f_no_max
FROM line_scan_lens_4k7u
WHERE f_no_max ~ '^\d+(\.\d+)?$';
```

---

## Notes

- **Primary Key:** `model_name`
- **Important anomaly:** `f_no_max` is stored as `text` in this table, unlike all other line scan lens tables where it is `numeric`. Always inspect or cast before numeric filtering.
- `tv_distortion_operator` and `relative_illuminance_operator` are qualifier columns — always pair with their `_percent` counterparts.
- `fov_mm` is text type — use string operations or cast for numeric filtering.
- RAG hint: relevant to queries mentioning "4K", "4000 pixel", "7 micron", "7µm line scan".

---

---

# Table: line_scan_lens_8k5u

## Purpose

Stores specifications for **line scan lenses designed for 8K resolution sensors with 5 µm pixel pitch**. These lenses are used in mid-to-high resolution continuous web inspection, pharmaceutical blister pack inspection, and film/foil surface quality systems. The 8K/5µm combination balances scan width and resolution.

This table supports engineering selection by focal length, working distance, field of view, magnification, aperture, mount, filter thread, relative illuminance, and physical dimensions.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length in millimeters | numeric | Core optical parameter. Units: mm. |
| list_price | Catalogue price | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of maximum supported image/sensor size | text | Original string. |
| max_image_size_value | Numeric extracted maximum image size | numeric | Filtering dimension for sensor coverage. |
| f_no_raw | Raw text F-number range | text | Original aperture string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = more light. |
| f_no_max | Maximum F-number (smallest aperture) | numeric | Higher = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion | text | Qualifier column paired with `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion in percent | numeric | Geometric distortion metric. |
| fov_mm | Field of view in millimeters (linear) | text | Coverage width at object plane. Text type. Units: mm. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| standard_magnification | Standard nominal magnification | text | Reference magnification value label. |
| wd_mm | Working distance from lens to target in millimeters | numeric | Mounting clearance. Units: mm. |
| o_i | Object-to-image distance or total conjugate | numeric | Optical path metric. |
| flange_distance | Camera flange to sensor distance in millimeters | numeric | Camera compatibility. Units: mm. |
| mount_raw | Raw text of camera mount type | text | Mount compatibility identifier. |
| filter_thread_raw | Raw text of filter thread specification | text | Filter compatibility. |
| relative_illuminance_operator | Comparison operator for relative illuminance | text | Qualifier for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at field edge as percentage of center | numeric | Field uniformity metric. Units: %. |
| size_raw | Raw text of physical lens dimensions | text | Original formatted string. |
| size_diameter_mm | Physical outer diameter in millimeters | numeric | Space/clearance dimension. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens in millimeters | numeric | Minimum length bound. Units: mm. |
| weight_g | Physical weight in grams | numeric | Mounting load. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_8k5u` ↔ `line_scan_lens_12k5u`, `line_scan_lens_16k5u`
* All three target 5 µm pixel pitch sensors at increasing resolution tiers (8K, 12K, 16K). Suitable for resolution upgrade path analysis.
* `line_scan_lens_8k5u` ↔ `line_scan_lens_8k7u`
* Both cover 8K resolution but at different pixel pitches (5 µm vs. 7 µm). Useful for comparing lens options for different 8K camera models.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 8K 5µm lenses with focal length, standard magnification, and list price.

Reasoning:
- Retrieve three specification columns and the model identifier.

```sql
SELECT model_name, focus_length_mm, standard_magnification, list_price
FROM line_scan_lens_8k5u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 8K 5µm lenses with TV distortion less than or equal to 0.1%.

Reasoning:
- Filter `tv_distortion_percent` for low-distortion lenses.
- Also retrieve `tv_distortion_operator` for context.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator
FROM line_scan_lens_8k5u
WHERE tv_distortion_percent <= 0.1;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 8K 5µm lenses have a diameter under 60 mm and support a filter thread?

Reasoning:
- Filter `size_diameter_mm` for compact form factor.
- Filter `filter_thread_raw` for filter support.

```sql
SELECT model_name, size_diameter_mm, filter_thread_raw
FROM line_scan_lens_8k5u
WHERE size_diameter_mm < 60
  AND filter_thread_raw IS NOT NULL;
```

---

**4. Working Distance Search**

Natural Language:
Show all 8K 5µm lenses with working distance greater than 200 mm.

Reasoning:
- Filter `wd_mm` for long-range mounting requirements.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_8k5u
WHERE wd_mm > 200;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What does "relative illuminance" mean, and which 8K 5µm lenses have the best edge-to-center brightness uniformity?

Reasoning:
- `relative_illuminance_percent` measures how much light reaches the image edge relative to the center.
- Higher % = more uniform = less vignetting.
- Sort descending to find the most uniform lenses.

```sql
SELECT model_name, relative_illuminance_percent
FROM line_scan_lens_8k5u
ORDER BY relative_illuminance_percent DESC;
```

---

## Notes

- **Primary Key:** `model_name`
- `fov_mm` is stored as text — use `CAST` or `REGEXP` for numeric comparisons.
- `size_length_min_mm` is a minimum length bound, suggesting some models may be mechanically adjustable.
- `relative_illuminance_operator` paired with `relative_illuminance_percent` follows the convention used across most line scan lens tables.
- RAG hint: relevant to "8K 5µm", "8000 pixel 5 micron", "mid resolution line scan" queries.

---

---

# Table: line_scan_lens_8k7u

## Purpose

Stores specifications for **line scan lenses designed for 8K resolution sensors with 7 µm pixel pitch**. These lenses are well-suited for high-speed applications where larger pixel sizes are preferred for better light sensitivity — for instance in low-light inspection of paper, textiles, or food surfaces at high throughput speeds.

This table also uniquely includes a `fov_degrees` column, indicating angular field of view, in addition to the standard linear `fov_mm`.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length in millimeters | numeric | Core optical parameter. Units: mm. |
| list_price | Catalogue price | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of maximum supported sensor/image size | text | Original string. |
| max_image_size_value | Numeric extracted maximum image size | numeric | Sensor coverage filtering dimension. |
| f_no_raw | Raw text F-number range | text | Original aperture specification string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = more light admitted. |
| f_no_max | Maximum F-number (smallest aperture) | numeric | Higher = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion | text | Qualifier paired with `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion in percent | numeric | Geometric distortion metric. |
| fov_mm | Field of view in millimeters (linear) at object plane | text | Coverage width. Text type. Units: mm. |
| fov_degrees | Field of view in degrees (angular) | numeric | Angular coverage metric. Units: degrees. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| standard_magnification | Standard or nominal magnification reference | text | Text label. |
| wd_mm | Working distance from lens front to object in millimeters | numeric | Mounting clearance. Units: mm. |
| o_i | Object-to-image distance or total conjugate | numeric | Optical path metric. |
| flange_distance | Camera flange to sensor distance in millimeters | numeric | Camera-side compatibility. Units: mm. |
| mount_raw | Raw text of camera mount type | text | Mount compatibility label. |
| filter_thread_raw | Raw text of filter thread specification | text | Filter compatibility. |
| relative_illuminance_operator | Comparison operator for relative illuminance | text | Qualifier for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at field edge as percentage of center | numeric | Field uniformity. Units: %. |
| size_raw | Raw text of physical lens dimensions | text | Original formatted string. |
| size_diameter_mm | Physical outer diameter in millimeters | numeric | Clearance dimension. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens in millimeters | numeric | Minimum length bound. Units: mm. |
| weight_g | Physical weight in grams | numeric | Mounting load. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `line_scan_lens_8k7u` ↔ `line_scan_lens_4k7u`, `new_series_line_scan_lens_4k7u`
* All three target 7 µm pixel pitch sensors. Cross-table comparison enables resolution tier selection (4K vs. 8K) for the same camera pixel size family.
* `line_scan_lens_8k7u` ↔ `line_scan_lens_8k5u`
* Both target 8K resolution at different pixel pitches (7 µm vs. 5 µm). Useful for selecting between camera models with same resolution but different sensor designs.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 8K 7µm lenses with focal length, angular field of view, and flange distance.

Reasoning:
- Select the key specification columns for all models.

```sql
SELECT model_name, focus_length_mm, fov_degrees, flange_distance
FROM line_scan_lens_8k7u;
```

---

**2. Attribute Filtering**

Natural Language:
Find 8K 7µm lenses with an outer diameter of 60 mm or less and weight under 400 g.

Reasoning:
- Filter `size_diameter_mm` and `weight_g` for compact, lightweight options.

```sql
SELECT model_name, size_diameter_mm, weight_g
FROM line_scan_lens_8k7u
WHERE size_diameter_mm <= 60
  AND weight_g < 400;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 8K 7µm lenses have a maximum F-number above 16 and support sensor sizes larger than 40 mm?

Reasoning:
- Filter `f_no_max` for lenses with a wide aperture range.
- Filter `max_image_size_value` for large sensor coverage.

```sql
SELECT model_name, f_no_max, max_image_size_value
FROM line_scan_lens_8k7u
WHERE f_no_max > 16
  AND max_image_size_value > 40;
```

---

**4. Working Distance Search**

Natural Language:
Show 8K 7µm lenses with working distance between 80 mm and 200 mm.

Reasoning:
- Range filter on `wd_mm`.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM line_scan_lens_8k7u
WHERE wd_mm BETWEEN 80 AND 200;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What is "o_i" in this table and how does it relate to total lens track length?

Reasoning:
- `o_i` is the object-to-image distance (total conjugate distance), representing the full optical path from object to image sensor.
- `flange_distance` represents only the camera-side portion.
- Comparing `o_i` vs. `wd_mm + flange_distance` reveals internal lens element spacing.

```sql
SELECT model_name, o_i, wd_mm, flange_distance
FROM line_scan_lens_8k7u;
```

---

## Notes

- **Primary Key:** `model_name`
- `fov_degrees` is numeric in this table, allowing direct arithmetic (e.g., half-angle = `fov_degrees / 2`).
- `fov_mm` is still text — use `CAST` for numeric operations.
- `size_length_min_mm` is a minimum bound, consistent with other line scan tables.
- RAG hint: relevant to "8K 7µm", "8000 pixel 7 micron", "large pixel high speed line scan" queries.

---

---

# Table: new_series_line_scan_lens_4k7u

## Purpose

Stores specifications for a **new product series of line scan lenses targeting 4K resolution sensors with 7 µm pixel pitch**. This is a generational update or product refresh relative to `line_scan_lens_4k7u`, offering potentially improved optical performance, updated coatings, or revised mechanical design for the same sensor format.

This table supports engineering selection by focal length, working distance, field of view, magnification, aperture, mount, filter thread, relative illuminance, and physical size.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier | text | Primary key. Main lookup identifier. |
| focus_length_mm | Focal length in millimeters | numeric | Core optical parameter. Units: mm. |
| list_price | Catalogue price | numeric | Monetary value. Assumed USD. |
| max_image_size_raw | Raw text of maximum supported image/sensor size | text | Original string. |
| max_image_size_value | Numeric extracted maximum image size | numeric | Sensor coverage filtering dimension. |
| f_no_raw | Raw text F-number range | text | Original aperture specification string. |
| f_no_min | Minimum F-number (widest aperture) | numeric | Lower = more light. |
| f_no_max | Maximum F-number (smallest aperture) | numeric | Higher = greater depth of field. Numeric type (unlike original 4k7u table). |
| tv_distortion_operator | Comparison operator for TV distortion | text | Qualifier paired with `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion in percent | numeric | Geometric distortion metric. |
| fov_raw | Raw text field of view specification | text | Original source string. |
| fov_degrees | Field of view in degrees (angular) | numeric | Angular coverage. Units: degrees. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| standard_magnification | Standard or nominal magnification reference | text | Text label. |
| wd_mm | Working distance from lens to target in millimeters | numeric | Mounting clearance. Units: mm. |
| flange_distance | Camera flange to sensor distance in millimeters | numeric | Camera compatibility. Units: mm. |
| mount_raw | Raw text of camera mount type | text | Mount compatibility label. |
| filter_thread_raw | Raw text of filter thread specification | text | Filter compatibility. |
| relative_illuminance_operator | Comparison operator for relative illuminance | text | Qualifier for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at field edge as percentage of center | numeric | Field uniformity metric. Units: %. |
| size_raw | Raw text of physical lens dimensions | text | Original formatted string. |
| size_diameter_mm | Physical outer diameter in millimeters | numeric | Clearance dimension. Units: mm. |
| size_length_min_mm | Minimum physical length of the lens in millimeters | numeric | Minimum length bound. Units: mm. |
| weight_g | Physical weight in grams | numeric | Mounting load. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `new_series_line_scan_lens_4k7u` ↔ `line_scan_lens_4k7u`
* Direct generational counterpart. Same sensor target (4K / 7 µm). Cross-table comparison reveals product generation differences. The new series adds `fov_raw`, `fov_degrees`, and has `f_no_max` as numeric (not text).
* `new_series_line_scan_lens_4k7u` ↔ `line_scan_lens_8k7u`
* Same 7 µm pixel pitch family at different resolutions (4K vs. 8K).

---

## Example Queries

**1. Specification Lookup**

Natural Language:
Show all new series 4K 7µm lenses with their angular field of view and standard magnification.

Reasoning:
- Select `fov_degrees` and `standard_magnification` alongside the identifier.

```sql
SELECT model_name, fov_degrees, standard_magnification
FROM new_series_line_scan_lens_4k7u;
```

---

**2. Attribute Filtering**

Natural Language:
Find new series 4K 7µm lenses with relative illuminance greater than 55% and TV distortion below 0.1%.

Reasoning:
- Combined filter on `relative_illuminance_percent` and `tv_distortion_percent`.

```sql
SELECT model_name, relative_illuminance_percent, tv_distortion_percent
FROM new_series_line_scan_lens_4k7u
WHERE relative_illuminance_percent > 55
  AND tv_distortion_percent < 0.1;
```

---

**3. Compatibility Reasoning**

Natural Language:
Compare new series 4K 7µm lenses by filter thread size — which models support filters?

Reasoning:
- Retrieve `filter_thread_raw` for all models; null values mean no filter support.

```sql
SELECT model_name, filter_thread_raw, mount_raw
FROM new_series_line_scan_lens_4k7u
WHERE filter_thread_raw IS NOT NULL;
```

---

**4. Working Distance Search**

Natural Language:
List new series 4K 7µm lenses with working distance between 50 mm and 150 mm.

Reasoning:
- Range filter on `wd_mm` for short-to-mid range integration.

```sql
SELECT model_name, wd_mm, focus_length_mm
FROM new_series_line_scan_lens_4k7u
WHERE wd_mm BETWEEN 50 AND 150;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
How does this new series compare to the original 4K 7µm series on maximum aperture (f_no_min)?

Reasoning:
- The original `line_scan_lens_4k7u` also has `f_no_min`. Joining or unioning the two on `f_no_min` enables a cross-generation aperture comparison.

```sql
SELECT 'original' AS series, model_name, f_no_min
FROM line_scan_lens_4k7u
UNION ALL
SELECT 'new_series' AS series, model_name, f_no_min
FROM new_series_line_scan_lens_4k7u
ORDER BY f_no_min;
```

---

## Notes

- **Primary Key:** `model_name`
- Key structural difference from `line_scan_lens_4k7u`: `f_no_max` is `numeric` here (not `text`), and `fov_degrees` is present.
- `o_i` is absent from this table (present in the original 4k7u). Optical conjugate distance calculations cannot be done directly.
- RAG hint: relevant to "new series 4K 7µm", "updated 4K line scan lens", "4000 pixel 7 micron new generation" queries.

---