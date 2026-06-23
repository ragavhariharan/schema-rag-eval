# Telecentric Lens Schema Documentation
> RAG-ready knowledge base for machine vision telecentric lens database tables.
> All tables use `model_name` as the primary key. No foreign key relationships exist across tables.

---

# Table: standard_telecentric_lenses_1_1_inch

## Purpose

Stores specifications for **standard telecentric lenses designed around a 1.1-inch primary sensor format**. Telecentric lenses maintain constant magnification regardless of object distance and produce parallel chief rays, eliminating perspective error — making them essential for precision dimensional measurement, gauging, and inspection of parts with varying height (Z-axis variation) such as machined components, connectors, and stamped metal parts.

This table is distinctive in that it reports field of view (FOV) across three different sensor formats (1.1", 1", and 2/3") for the same lens model, allowing a single lens to be evaluated against multiple camera sensor options. It supports engineering lookups for selecting lenses by magnification, working distance, telecentricity, depth of field, aperture, and physical dimensions.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| price_usd | Base price in **USD** (the `list_price` column is the INR retail price) | text | Original source string; may include currency symbols or formatting. Preserved for display. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. Derived from `price_usd` (the base USD price) × markup × the USD→INR dollar rate (~95.5), so `list_price` ≠ `price_usd`. |
| illumination_type | Type of integrated illumination, if any | text | E.g., "coaxial", "none". Null or "none" indicates no integrated illumination. |
| sensor_raw | Raw text representation of the compatible sensor size | text | Original source string, may include formats like "1.1 inch" or "2/3\"". |
| magnification_raw | Raw text representation of the lens magnification | text | Original source string (e.g., "0.5×"). |
| magnification_value | Numeric extracted magnification ratio | numeric | Dimensionless ratio. Telecentric lenses are typically fixed-magnification (not a range). |
| wd_mm | Working distance between the lens front element and the object/target surface, measured in millimeters | numeric | Fixed value for most telecentric lenses since magnification is constant. Units: mm. |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F8 – F16"). Preserved for display. |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| nd | Neutral density factor, if applicable | numeric | Indicates light attenuation factor for an integrated or optional ND filter element; null if not applicable. |
| telecentricity_operator | Comparison operator associated with the telecentricity value | text | E.g., "<", "≤". Used to interpret whether `telecentricity_degrees` is a maximum bound or exact value. |
| telecentricity_degrees | Telecentricity error expressed in degrees | numeric | Lower values indicate better telecentricity (more parallel chief rays), critical for accurate dimensional measurement. Units: degrees. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Measures geometric distortion of the lens. Lower absolute value = less distortion. Negative values indicate barrel distortion; positive values indicate pincushion distortion. |
| dof_mm | Depth of field in millimeters | numeric | Range over which the object remains in acceptable focus. Telecentric lenses typically report a single DOF value at the design working distance. Units: mm. |
| object_side_resolution_um | Object-side resolving power | text | Original source string, may include units (e.g., "5 μm"). Stored as text — may contain formatting or symbols. |
| ttl | Total track length (lens mount flange to image plane along optical axis) | numeric | Used for mechanical clearance and back focal distance calculations. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount) | text | Determines mechanical and optical compatibility with camera. |
| fov_1_1_inch_raw | Raw text representation of the field of view for a 1.1-inch sensor | text | Original source string. |
| fov_1_1_inch_d | Diagonal field of view for a 1.1-inch sensor | numeric | Diagonal FOV measurement at the design working distance. Units: mm. |
| fov_1_1_inch_h | Horizontal field of view for a 1.1-inch sensor | numeric | Horizontal FOV measurement. Units: mm. |
| fov_1_1_inch_v | Vertical field of view for a 1.1-inch sensor | numeric | Vertical FOV measurement. Units: mm. |
| fov_1_inch_raw | Raw text representation of the field of view for a 1-inch sensor | text | Original source string. |
| fov_1_inch_h | Horizontal field of view for a 1-inch sensor | numeric | Horizontal FOV measurement when paired with a 1-inch sensor camera. Units: mm. |
| fov_1_inch_v | Vertical field of view for a 1-inch sensor | numeric | Vertical FOV measurement when paired with a 1-inch sensor camera. Units: mm. |
| fov_2_3_inch_raw | Raw text representation of the field of view for a 2/3-inch sensor | text | Original source string. |
| fov_2_3_inch_h | Horizontal field of view for a 2/3-inch sensor | numeric | Horizontal FOV measurement when paired with a 2/3-inch sensor camera. Units: mm. |
| fov_2_3_inch_v | Vertical field of view for a 2/3-inch sensor | numeric | Vertical FOV measurement when paired with a 2/3-inch sensor camera. Units: mm. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string, may include diameter and length combined (e.g., "Ø65 × 120 mm"). |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `standard_telecentric_lenses_1_1_inch` ↔ `standard_telecentric_lenses_2_3_inch`, `telecentric_lenses_65mp`, `non_standard_telecentric_lenses`
* All telecentric lens tables share common optical specification columns (`magnification_value`, `wd_mm`, `f_no_min`, `f_no_max`, `telecentricity_degrees`, `tv_distortion_percent`, `dof_mm`, `mount_raw`, `size_diameter_mm`, `size_length_mm`).
* This table is distinguished by reporting FOV across three sensor formats (1.1", 1", 2/3") for the same lens — useful when a customer's camera sensor format is undecided or when comparing coverage across multiple camera options.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What is the magnification, working distance, and telecentricity of all standard 1.1-inch telecentric lenses?

Reasoning:
- Select the identifying column and the three requested specification columns.
- No filtering needed — return all rows.

```sql
SELECT model_name, magnification_value, wd_mm, telecentricity_degrees
FROM standard_telecentric_lenses_1_1_inch;
```

---

**2. Attribute Filtering**

Natural Language:
Find all 1.1-inch telecentric lenses with a telecentricity error of less than 0.05 degrees.

Reasoning:
- Filter on `telecentricity_degrees` for high-precision measurement applications.
- Lower telecentricity error = better suited for accurate dimensional gauging.

```sql
SELECT model_name, telecentricity_degrees, telecentricity_operator
FROM standard_telecentric_lenses_1_1_inch
WHERE telecentricity_degrees < 0.05;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 1.1-inch telecentric lenses provide a horizontal FOV of at least 50mm on a 1-inch sensor and use a C-mount?

Reasoning:
- Filter `fov_1_inch_h` for sufficient horizontal coverage on a 1-inch sensor.
- Filter `mount_raw` for C-mount compatibility.

```sql
SELECT model_name, fov_1_inch_h, mount_raw
FROM standard_telecentric_lenses_1_1_inch
WHERE fov_1_inch_h >= 50
  AND mount_raw ILIKE '%C%';
```

---

**4. Working Distance Search**

Natural Language:
List all 1.1-inch telecentric lenses with a working distance greater than 100 mm.

Reasoning:
- Filter on `wd_mm` to find lenses suitable for applications requiring clearance between lens and target.

```sql
SELECT model_name, wd_mm, magnification_value
FROM standard_telecentric_lenses_1_1_inch
WHERE wd_mm > 100;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What does field of view look like for the same lens across different sensor sizes — show 1.1-inch, 1-inch, and 2/3-inch FOV side by side.

Reasoning:
- This table is unique in storing FOV for three sensor formats simultaneously.
- Retrieving all three side by side clarifies how the same optical design covers different sensor sizes.

```sql
SELECT model_name,
       fov_1_1_inch_h, fov_1_1_inch_v,
       fov_1_inch_h, fov_1_inch_v,
       fov_2_3_inch_h, fov_2_3_inch_v
FROM standard_telecentric_lenses_1_1_inch;
```

---

**6. Depth of Field Search**

Natural Language:
Find 1.1-inch telecentric lenses with a depth of field greater than 5mm, suitable for parts with height variation.

Reasoning:
- Filter on `dof_mm` to identify lenses tolerant of Z-axis variation in the target.

```sql
SELECT model_name, dof_mm, magnification_value
FROM standard_telecentric_lenses_1_1_inch
WHERE dof_mm > 5;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `telecentricity_degrees` should be interpreted alongside `telecentricity_operator` to determine if it represents a maximum bound or a typical/exact value.
- This table uniquely lacks `fov_1_1_inch_raw`-paired numeric diagonal values for the 1-inch and 2/3-inch formats — only the 1.1-inch format includes a diagonal (`fov_1_1_inch_d`); the 1-inch and 2/3-inch formats report horizontal and vertical only.
- `price_usd`, `sensor_raw`, `magnification_raw`, `object_side_resolution_um`, `fov_1_1_inch_raw`, `fov_1_inch_raw`, `fov_2_3_inch_raw`, and `size_raw` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "C").
- **No `weight_g` column** in this table — unlike the 2/3-inch standard telecentric table, physical weight is not tracked here.
- This table is optimized for RAG chunk retrieval when queries mention "telecentric", "1.1 inch telecentric", "constant magnification lens", or "parallel ray lens".

---

---

# Table: standard_telecentric_lenses_2_3_inch

## Purpose

Stores specifications for **standard telecentric lenses designed around a 2/3-inch primary sensor format**. Like other telecentric lenses, these maintain constant magnification regardless of object distance and eliminate perspective error, making them suitable for precision measurement and inspection where consistent scale across the field of view is critical, such as electronics component inspection and small parts gauging.

This table reports field of view across three sensor formats (2/3", 1/1.8", 1/2") for the same lens model, and — unlike the 1.1-inch standard table — also tracks lens weight.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| price_usd | Base price in **USD** (the `list_price` column is the INR retail price) | text | Original source string; may include currency symbols or formatting. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. Derived from `price_usd` (the base USD price) × markup × the USD→INR dollar rate (~95.5), so `list_price` ≠ `price_usd`. |
| illumination_type | Type of integrated illumination, if any | text | E.g., "coaxial", "none". Null or "none" indicates no integrated illumination. |
| sensor_raw | Raw text representation of the compatible sensor size | text | Original source string, may include formats like "2/3 inch". |
| magnification_raw | Raw text representation of the lens magnification | text | Original source string (e.g., "1.0×"). |
| magnification_value | Numeric extracted magnification ratio | numeric | Dimensionless ratio. Fixed value typical of telecentric lens design. |
| wd_mm | Working distance between the lens front element and the object/target surface, measured in millimeters | numeric | Fixed design working distance. Units: mm. |
| f_no_raw | Raw text representation of the F-number specification | text | Original source string (e.g., "F8"). |
| f_no_value | Single F-number value for the lens | numeric | Unlike the 1.1-inch and other tables, this table stores a single fixed F-number rather than a min/max range. |
| nd | Neutral density factor, if applicable | numeric | Indicates light attenuation factor for an integrated or optional ND filter element; null if not applicable. |
| telecentricity_operator | Comparison operator associated with the telecentricity value | text | E.g., "<", "≤". Used to interpret whether `telecentricity_degrees` is a maximum bound or exact value. |
| telecentricity_degrees | Telecentricity error expressed in degrees | numeric | Lower values indicate better telecentricity. Units: degrees. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Geometric distortion metric. Lower absolute value = less distortion. Negative = barrel; positive = pincushion. |
| dof_mm | Depth of field in millimeters | numeric | Range over which the object remains in acceptable focus at the design working distance. Units: mm. |
| object_side_resolution_um | Object-side resolving power | text | Original source string, may include units (e.g., "3 μm"). Stored as text. |
| ttl | Total track length (lens mount flange to image plane along optical axis) | numeric | Mechanical clearance and back focal distance metric. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount) | text | Determines mechanical and optical compatibility with camera. |
| fov_2_3_inch_raw | Raw text representation of the field of view for a 2/3-inch sensor | text | Original source string. |
| fov_2_3_inch_d | Diagonal field of view for a 2/3-inch sensor | numeric | Diagonal FOV measurement. Units: mm. |
| fov_2_3_inch_h | Horizontal field of view for a 2/3-inch sensor | numeric | Horizontal FOV measurement. Units: mm. |
| fov_2_3_inch_v | Vertical field of view for a 2/3-inch sensor | numeric | Vertical FOV measurement. Units: mm. |
| fov_1_1_8_inch_raw | Raw text representation of the field of view for a 1/1.8-inch sensor | text | Original source string. |
| fov_1_1_8_inch_d | Diagonal field of view for a 1/1.8-inch sensor | numeric | Diagonal FOV measurement when paired with a 1/1.8-inch sensor camera. Units: mm. |
| fov_1_1_8_inch_h | Horizontal field of view for a 1/1.8-inch sensor | numeric | Horizontal FOV measurement. Units: mm. |
| fov_1_1_8_inch_v | Vertical field of view for a 1/1.8-inch sensor | numeric | Vertical FOV measurement. Units: mm. |
| fov_1_2_inch_raw | Raw text representation of the field of view for a 1/2-inch sensor | text | Original source string. |
| fov_1_2_inch_d | Diagonal field of view for a 1/2-inch sensor | numeric | Diagonal FOV measurement when paired with a 1/2-inch sensor camera. Units: mm. |
| fov_1_2_inch_h | Horizontal field of view for a 1/2-inch sensor | numeric | Horizontal FOV measurement. Units: mm. |
| fov_1_2_inch_v | Vertical field of view for a 1/2-inch sensor | numeric | Vertical FOV measurement. Units: mm. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string, may include diameter and length combined. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress and robotic integration. Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `standard_telecentric_lenses_2_3_inch` ↔ `standard_telecentric_lenses_1_1_inch`
* Both are "standard" telecentric lens families differing in primary sensor target size (2/3" vs. 1.1"). Cross-table comparison helps identify the appropriate lens family for a target sensor size.
* `standard_telecentric_lenses_2_3_inch` ↔ `telecentric_lenses_65mp`, `non_standard_telecentric_lenses`
* Shares common optical specification columns (`magnification_value`, `wd_mm`, `telecentricity_degrees`, `tv_distortion_percent`, `dof_mm`, `mount_raw`) with the broader telecentric lens family.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 2/3-inch telecentric lenses with magnification, working distance, and weight.

Reasoning:
- Select the four relevant columns for all models.

```sql
SELECT model_name, magnification_value, wd_mm, weight_g
FROM standard_telecentric_lenses_2_3_inch;
```

---

**2. Attribute Filtering**

Natural Language:
Find 2/3-inch telecentric lenses with an F-number of 8 or lower.

Reasoning:
- Filter on `f_no_value`, the single fixed F-number for this table (no min/max range here).

```sql
SELECT model_name, f_no_value, f_no_raw
FROM standard_telecentric_lenses_2_3_inch
WHERE f_no_value <= 8;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 2/3-inch telecentric lenses provide a horizontal FOV of at least 20mm on a 1/2-inch sensor and use a C-mount?

Reasoning:
- Filter `fov_1_2_inch_h` for sufficient horizontal coverage on the smaller 1/2-inch sensor format.
- Filter `mount_raw` for C-mount compatibility.

```sql
SELECT model_name, fov_1_2_inch_h, mount_raw
FROM standard_telecentric_lenses_2_3_inch
WHERE fov_1_2_inch_h >= 20
  AND mount_raw ILIKE '%C%';
```

---

**4. Working Distance Search**

Natural Language:
Show all 2/3-inch telecentric lenses with a working distance between 50 mm and 150 mm.

Reasoning:
- Range filter on `wd_mm` to identify lenses fitting a specific mounting envelope.

```sql
SELECT model_name, wd_mm, magnification_value
FROM standard_telecentric_lenses_2_3_inch
WHERE wd_mm BETWEEN 50 AND 150;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
How does diagonal FOV compare across the three supported sensor formats (2/3", 1/1.8", 1/2") for each lens?

Reasoning:
- This table uniquely stores diagonal FOV (`_d` suffix) for all three sensor formats, unlike the 1.1-inch table which only has a diagonal value for its primary format.
- Retrieving all three diagonal values side by side shows coverage scaling across sensor sizes.

```sql
SELECT model_name, fov_2_3_inch_d, fov_1_1_8_inch_d, fov_1_2_inch_d
FROM standard_telecentric_lenses_2_3_inch;
```

---

**6. Mechanical Fit Search**

Natural Language:
Find 2/3-inch telecentric lenses with a diameter under 60mm and weight below 500 grams.

Reasoning:
- Filter `size_diameter_mm` and `weight_g` for compact, lightweight integration options.

```sql
SELECT model_name, size_diameter_mm, weight_g
FROM standard_telecentric_lenses_2_3_inch
WHERE size_diameter_mm < 60
  AND weight_g < 500;
```

---

## Notes

- **Primary Key:** `model_name`
- **Key structural difference from `standard_telecentric_lenses_1_1_inch`:** this table stores a single `f_no_value` rather than `f_no_min`/`f_no_max`, and includes diagonal FOV (`_d`) for all three sensor formats rather than just the primary one.
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `price_usd`, `sensor_raw`, `magnification_raw`, `object_side_resolution_um`, all `fov_*_raw` columns, and `size_raw` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "C").
- This table includes `weight_g`, unlike `standard_telecentric_lenses_1_1_inch`.
- This table is optimized for RAG chunk retrieval when queries mention "telecentric", "2/3 inch telecentric", "constant magnification lens", or "parallel ray lens".

---

---

# Table: telecentric_lenses_65mp

## Purpose

Stores specifications for **telecentric lenses designed for 65-megapixel-class high-resolution sensors**. These lenses target the highest-resolution telecentric applications, such as fine-pitch PCB inspection, flat panel display sub-pixel inspection, and semiconductor packaging inspection, where both telecentricity and very high resolving power are required simultaneously. This table is unique among the telecentric tables in including a numeric `sensor_value`, `flange_distance`, and coating band (spectral bandpass) specification.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| price_usd | Base price in **USD** (the `list_price` column is the INR retail price) | text | Original source string; may include currency symbols or formatting. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. Derived from `price_usd` (the base USD price) × markup × the USD→INR dollar rate (~95.5), so `list_price` ≠ `price_usd`. |
| illumination_type | Type of integrated illumination, if any | text | E.g., "coaxial", "none". Null or "none" indicates no integrated illumination. |
| sensor_raw | Raw text representation of the compatible sensor size | text | Original source string, may include formats like "1.4 inch" or megapixel labels. |
| sensor_value | Numeric extracted value of the compatible sensor size or rating | numeric | Parsed numeric dimension or megapixel value for filtering. |
| magnification_raw | Raw text representation of the lens magnification | text | Original source string (e.g., "1.5×"). |
| magnification_value | Numeric extracted magnification ratio | numeric | Dimensionless ratio. |
| wd_mm | Working distance between the lens front element and the object/target surface, measured in millimeters | numeric | Fixed design working distance. Units: mm. |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F8 – F16"). |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| nd | Neutral density factor, if applicable | numeric | Indicates light attenuation factor for an integrated or optional ND filter element; null if not applicable. |
| telecentricity_operator | Comparison operator associated with the telecentricity value | text | E.g., "<", "≤". Used to interpret whether `telecentricity_degrees` is a maximum bound or exact value. |
| telecentricity_degrees | Telecentricity error expressed in degrees | numeric | Lower values indicate better telecentricity, critical at high resolution where even small angular errors cause measurable parallax. Units: degrees. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Geometric distortion metric. Lower absolute value = less distortion. |
| dof_mm | Depth of field in millimeters | numeric | Range over which the object remains in acceptable focus. Typically very shallow at 65MP-class resolution and higher magnification. Units: mm. |
| object_side_resolution_um | Object-side resolving power | text | Original source string, may include units (e.g., "2 μm"). Stored as text. |
| ttl | Total track length (lens mount flange to image plane along optical axis) | numeric | Mechanical clearance and back focal distance metric. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount, M42) | text | Determines mechanical and optical compatibility with camera. |
| flange_distance | Distance from the camera mounting flange to the image sensor plane, measured in millimeters | numeric | Used to confirm physical compatibility with camera body. Unique to this table among the telecentric lens tables. Units: mm. |
| fov_raw | Raw text representation of the field of view | text | Original source string. |
| fov_d | Diagonal field of view | numeric | Diagonal FOV measurement at the design working distance. Units: mm. |
| fov_h | Horizontal field of view | numeric | Horizontal FOV measurement. Units: mm. |
| fov_v | Vertical field of view | numeric | Vertical FOV measurement. Units: mm. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |
| coating_band_raw | Raw text representation of the optical coating spectral bandpass | text | Original source string (e.g., "400 – 700 nm"). Indicates the wavelength range over which the anti-reflective coating is optimized. |
| coating_band_min_nm | Minimum wavelength of the optical coating bandpass in nanometers | numeric | Lower bound of optimized transmission band. Units: nm. |
| coating_band_max_nm | Maximum wavelength of the optical coating bandpass in nanometers | numeric | Upper bound of optimized transmission band. Units: nm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `telecentric_lenses_65mp` ↔ `standard_telecentric_lenses_1_1_inch`, `standard_telecentric_lenses_2_3_inch`, `non_standard_telecentric_lenses`
* Shares common optical specification columns (`magnification_value`, `wd_mm`, `f_no_min`, `f_no_max`, `telecentricity_degrees`, `tv_distortion_percent`, `dof_mm`, `mount_raw`, `size_diameter_mm`, `size_length_mm`) with the broader telecentric lens family.
* Represents the highest-resolution tier of the telecentric lens family and may be cross-referenced when standard telecentric lenses do not meet resolution requirements for very high megapixel sensors.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the magnification, working distance, and object-side resolution of all 65MP telecentric lenses?

Reasoning:
- Select the identifying column and the three requested specification columns.

```sql
SELECT model_name, magnification_value, wd_mm, object_side_resolution_um
FROM telecentric_lenses_65mp;
```

---

**2. Attribute Filtering**

Natural Language:
Find 65MP telecentric lenses with a telecentricity error below 0.03 degrees.

Reasoning:
- Filter on `telecentricity_degrees` for ultra-precise measurement applications at high resolution.

```sql
SELECT model_name, telecentricity_degrees, telecentricity_operator
FROM telecentric_lenses_65mp
WHERE telecentricity_degrees < 0.03;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which 65MP telecentric lenses have a flange distance compatible with a standard C-mount camera (typically around 17.5mm) and support sensor sizes above 1 inch?

Reasoning:
- Filter `flange_distance` near the expected C-mount flange distance.
- Filter `sensor_value` for large sensor coverage.

```sql
SELECT model_name, flange_distance, sensor_value, mount_raw
FROM telecentric_lenses_65mp
WHERE flange_distance BETWEEN 17 AND 18
  AND sensor_value > 1;
```

---

**4. Working Distance Search**

Natural Language:
List all 65MP telecentric lenses with a working distance greater than 80 mm.

Reasoning:
- Filter on `wd_mm` to find lenses suitable for applications requiring clearance between lens and target.

```sql
SELECT model_name, wd_mm, magnification_value
FROM telecentric_lenses_65mp
WHERE wd_mm > 80;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What does the "coating band" mean for these lenses, and which models are optimized for near-infrared imaging above 800nm?

Reasoning:
- `coating_band_min_nm` and `coating_band_max_nm` define the spectral range over which the lens's anti-reflective coating is optimized.
- Filtering for a minimum band starting above 800nm identifies lenses suited for NIR imaging applications.

```sql
SELECT model_name, coating_band_raw, coating_band_min_nm, coating_band_max_nm
FROM telecentric_lenses_65mp
WHERE coating_band_min_nm >= 800;
```

---

**6. Depth of Field Search**

Natural Language:
Find 65MP telecentric lenses with a depth of field greater than 1mm, given that high-resolution telecentric lenses tend to have shallow DOF.

Reasoning:
- Filter on `dof_mm` to identify lenses more tolerant of focus variation despite high resolution.

```sql
SELECT model_name, dof_mm, magnification_value
FROM telecentric_lenses_65mp
WHERE dof_mm > 1;
```

---

## Notes

- **Primary Key:** `model_name`
- **Unique to this table:** `sensor_value`, `flange_distance`, and the `coating_band_*` columns are not present in the other telecentric lens tables.
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `price_usd`, `sensor_raw`, `magnification_raw`, `object_side_resolution_um`, `fov_raw`, `size_raw`, and `coating_band_raw` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "C").
- Unlike the standard telecentric tables, this table reports only a single FOV set (`fov_d`, `fov_h`, `fov_v`) rather than FOV across multiple sensor formats — appropriate since 65MP-class lenses are typically matched to one specific high-resolution sensor.
- This table is optimized for RAG chunk retrieval when queries mention "65MP telecentric", "high resolution telecentric", "fine pitch inspection lens", or "high megapixel telecentric".

---

---

# Table: non_standard_telecentric_lenses

## Purpose

Stores specifications for **non-standard (custom or specialty) telecentric lenses** that do not fit into the standard 1.1-inch, 2/3-inch, or 65MP product families. These may include custom magnifications, unusual sensor format targets, specialty mounts, or lenses developed for specific OEM/customer requirements. This table is the most feature-complete of the telecentric tables, combining attributes seen across the other three families: aperture range, telecentricity, weight, filter thread, and relative illuminance.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| price_usd | Base price in **USD** (the `list_price` column is the INR retail price) | text | Original source string; may include currency symbols or formatting. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. Derived from `price_usd` (the base USD price) × markup × the USD→INR dollar rate (~95.5), so `list_price` ≠ `price_usd`. |
| illumination_type | Type of integrated illumination, if any | text | E.g., "coaxial", "none". Null or "none" indicates no integrated illumination. |
| sensor_raw | Raw text representation of the compatible sensor size | text | Original source string. |
| magnification_raw | Raw text representation of the lens magnification | text | Original source string (e.g., "0.75×"). |
| magnification_value | Numeric extracted magnification ratio | numeric | Dimensionless ratio. |
| wd_mm | Working distance between the lens front element and the object/target surface, measured in millimeters | numeric | Fixed design working distance. Units: mm. |
| f_no_raw | Raw text representation of the F-number (aperture) range | text | Original source string (e.g., "F4 – F22"). |
| f_no_min | Minimum (most open) F-number supported by the lens | numeric | Lower F-number = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported by the lens | numeric | Higher F-number = smaller aperture = greater depth of field. |
| nd | Neutral density factor, if applicable | numeric | Indicates light attenuation factor for an integrated or optional ND filter element; null if not applicable. |
| telecentricity_operator | Comparison operator associated with the telecentricity value | text | E.g., "<", "≤". Used to interpret whether `telecentricity_degrees` is a maximum bound or exact value. |
| telecentricity_degrees | Telecentricity error expressed in degrees | numeric | Lower values indicate better telecentricity. Units: degrees. |
| tv_distortion_operator | Comparison operator associated with the TV distortion value | text | E.g., "<", "≤". Used to interpret whether `tv_distortion_percent` is a maximum bound or exact value. |
| tv_distortion_percent | TV distortion value expressed as a percentage | numeric | Geometric distortion metric. Lower absolute value = less distortion. |
| dof_mm | Depth of field in millimeters | numeric | Range over which the object remains in acceptable focus at the design working distance. Units: mm. |
| object_side_resolution_um | Object-side resolving power | text | Original source string, may include units (e.g., "4 μm"). Stored as text. |
| ttl | Total track length (lens mount flange to image plane along optical axis) | numeric | Mechanical clearance and back focal distance metric. Units: mm. |
| mount_raw | Raw text describing the camera mount type (e.g., C-mount, F-mount, custom) | text | Determines mechanical and optical compatibility with camera. |
| fov_raw | Raw text representation of the field of view | text | Original source string. |
| fov_d | Diagonal field of view | numeric | Diagonal FOV measurement at the design working distance. Units: mm. |
| fov_h | Horizontal field of view | numeric | Horizontal FOV measurement. Units: mm. |
| fov_v | Vertical field of view | numeric | Vertical FOV measurement. Units: mm. |
| size_raw | Raw text representation of the physical lens dimensions | text | Original source string. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Important for mounting clearance. Units: mm. |
| size_length_mm | Overall length of the lens body in millimeters | numeric | Important for housing and enclosure design. Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Important for mounting stress and robotic integration. Units: g. |
| filter_thread_raw | Raw text representation of the front filter thread size | text | Original source string (e.g., "M52 × 0.75"). Used for attaching filters or hoods. Unique to this table among the telecentric lens tables. |
| relative_illuminance_operator | Comparison operator associated with the relative illuminance value | text | E.g., "≥", ">". Used to interpret whether `relative_illuminance_percent` is a minimum bound or exact value. |
| relative_illuminance_percent | Relative illuminance at the edge of the image, expressed as a percentage of center illuminance | numeric | Higher values indicate more uniform brightness across the image circle. Unique to this table among the telecentric lens tables. Units: %. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `non_standard_telecentric_lenses` ↔ `standard_telecentric_lenses_1_1_inch`, `standard_telecentric_lenses_2_3_inch`, `telecentric_lenses_65mp`
* Shares common optical specification columns (`magnification_value`, `wd_mm`, `f_no_min`, `f_no_max`, `telecentricity_degrees`, `tv_distortion_percent`, `dof_mm`, `mount_raw`, `size_diameter_mm`, `size_length_mm`) with the broader telecentric lens family.
* Serves as a catch-all for telecentric lens models that fall outside the standard product families and is useful when a customer's requirement doesn't fit a standard sensor format or magnification.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
What are the magnification, working distance, and weight of all non-standard telecentric lenses?

Reasoning:
- Select the identifying column and the three requested specification columns.

```sql
SELECT model_name, magnification_value, wd_mm, weight_g
FROM non_standard_telecentric_lenses;
```

---

**2. Attribute Filtering**

Natural Language:
Find non-standard telecentric lenses with relative illuminance of at least 70% at the field edge.

Reasoning:
- Filter on `relative_illuminance_percent`, a column unique to this table among the telecentric lens family.
- Higher relative illuminance = more uniform brightness = less vignetting.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator
FROM non_standard_telecentric_lenses
WHERE relative_illuminance_percent >= 70;
```

---

**3. Compatibility Reasoning**

Natural Language:
Which non-standard telecentric lenses have a filter thread available and a maximum F-number above 16?

Reasoning:
- Filter `filter_thread_raw` for non-null values indicating filter support.
- Filter `f_no_max` for lenses offering a wide aperture range.

```sql
SELECT model_name, filter_thread_raw, f_no_max
FROM non_standard_telecentric_lenses
WHERE filter_thread_raw IS NOT NULL
  AND f_no_max > 16;
```

---

**4. Working Distance Search**

Natural Language:
List all non-standard telecentric lenses with a working distance under 60mm for close-range custom integrations.

Reasoning:
- Filter on `wd_mm` for short standoff distance requirements.

```sql
SELECT model_name, wd_mm, magnification_value
FROM non_standard_telecentric_lenses
WHERE wd_mm < 60;
```

---

**5. Ambiguous Engineering Terminology**

Natural Language:
What makes a telecentric lens "non-standard" — which models have magnification values that don't match common standard ratios like 0.5×, 1.0×, or 2.0×?

Reasoning:
- "Non-standard" in this context generally refers to custom magnifications, sensor targets, or mount types outside the standard product lines.
- Filtering for magnification values not equal to common standard ratios helps identify genuinely custom optical designs.

```sql
SELECT model_name, magnification_value, mount_raw
FROM non_standard_telecentric_lenses
WHERE magnification_value NOT IN (0.5, 1.0, 2.0);
```

---

**6. Mechanical Fit Search**

Natural Language:
Find non-standard telecentric lenses with a diameter under 80mm and weight below 600 grams.

Reasoning:
- Filter `size_diameter_mm` and `weight_g` for compact, lightweight custom integration options.

```sql
SELECT model_name, size_diameter_mm, weight_g
FROM non_standard_telecentric_lenses
WHERE size_diameter_mm < 80
  AND weight_g < 600;
```

---

## Notes

- **Primary Key:** `model_name`
- **Unique to this table among the telecentric family:** `filter_thread_raw` and the `relative_illuminance_operator`/`relative_illuminance_percent` pair.
- `tv_distortion_percent` may be positive (pincushion) or negative (barrel). Use `ABS()` for magnitude-only comparisons; check `tv_distortion_operator` for bound semantics.
- `relative_illuminance_percent` should be interpreted alongside `relative_illuminance_operator` to determine if it represents a guaranteed minimum or typical value.
- `price_usd`, `sensor_raw`, `magnification_raw`, `object_side_resolution_um`, `fov_raw`, `size_raw`, and `filter_thread_raw` are text fields — use `ILIKE` for pattern matching in SQL.
- `mount_raw` should be queried with `ILIKE` since format may vary (e.g., "C-Mount", "C mount", "custom mount").
- Unlike the standard telecentric tables, this table reports only a single FOV set (`fov_d`, `fov_h`, `fov_v`) rather than FOV across multiple sensor formats.
- This table is optimized for RAG chunk retrieval when queries mention "non-standard telecentric", "custom telecentric lens", "specialty telecentric", or "OEM telecentric lens".

---
