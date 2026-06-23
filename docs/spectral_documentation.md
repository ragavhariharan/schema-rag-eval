# Table: spectral_lenses

## Purpose

Stores specifications for **spectral lenses** — specialized optical lenses engineered for imaging across non-standard or extended wavelength ranges beyond the visible spectrum (400–700 nm). Spectral lenses are optimized for applications such as hyperspectral imaging, multispectral inspection, near-infrared (NIR) material analysis, ultraviolet (UV) fluorescence inspection, SWIR (short-wave infrared) imaging, and any machine vision task where the illumination or detection wavelength deviates from the standard broadband visible range.

Spectral lenses may be categorized by type (e.g., UV, NIR, SWIR, hyperspectral, broadband) and are distinguished from standard FA lenses by their anti-reflection coatings, glass selection, and optical design — all tuned to minimize chromatic aberration, transmission loss, and focus shift across their target wavelength band.

This table supports engineering lookups for selecting spectral lenses by spectral type, wavelength range, focal length, sensor size, aperture, magnification, distortion, field of view angles, flange distance, and physical dimensions. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| spectral_type | Classification of the lens by its target spectral band | text | E.g., "UV", "NIR", "SWIR", "hyperspectral", "broadband". Use `ILIKE` for filtering. |
| list_price | Catalogue sales price of the lens | numeric | Retail catalogue price in **INR (₹)**, NOT USD. In the source price list this is the base USD price × markup × the live USD→INR dollar rate (~95.5). |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string. Preserved for display. |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed dimension for filtering. Units: mm or inches depending on source context. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. Critical in low-radiance spectral bands (e.g., SWIR). |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| wavelength_raw | Raw text describing the supported wavelength range | text | Original source string (e.g., "400–1000 nm", "900–1700 nm"). Preserved for display. |
| wavelength_min_nm | Minimum supported wavelength in nanometers | numeric | Lower bound of the usable spectral range. Units: nm. E.g., 200 for deep UV, 900 for SWIR. |
| wavelength_max_nm | Maximum supported wavelength in nanometers | numeric | Upper bound of the usable spectral range. Units: nm. E.g., 1700 for SWIR InGaAs sensors. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string. Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. |
| mod_raw | Raw text for the Minimum Object Distance specification | text | Original source string. Preserved for display. |
| mod_distance_m | Minimum object distance in meters | numeric | Closest distance at which the lens can achieve focus. Units: m. |
| mod_magnification | Optical magnification at the minimum object distance | numeric | Dimensionless ratio. |
| flange_distance | Distance from camera mounting flange to image sensor plane | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M52×0.75". Use `ILIKE` for matching. |
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
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Units: mm. |
| size_length_max_mm | Maximum physical length of the lens body in millimeters | numeric | Units: mm. |
| weight_g | Physical weight of the lens body in grams | numeric | Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `spectral_lenses` ↔ `laser_coaxial_lenses`: both are wavelength-specific lens families. Laser coaxial lenses target a single wavelength; spectral lenses cover a defined wavelength band. Cross-reference by `wavelength_min_nm` / `wavelength_max_nm`.
* `spectral_lenses` ↔ `microscope_lenses`, `magnifying_lenses`: all three share `wavelength_min_nm` and `wavelength_max_nm` for spectral compatibility cross-referencing.
* `spectral_lenses` shares common optical columns (`focus_length_mm`, `f_no_min`, `f_no_max`, `mount_raw`, `max_image_size_value`) with `large_format_lenses` and `fa_lenses` for cross-family optical comparisons.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all spectral lenses with their spectral type, wavelength range, and focal length.

Reasoning:
- Select the most diagnostically useful columns for spectral lens identification.
- No filtering — return all rows.

```sql
SELECT model_name, spectral_type, wavelength_min_nm, wavelength_max_nm, focus_length_mm
FROM spectral_lenses;
```

---

**2. Spectral Type Filter**

Natural Language:
Find all NIR lenses in the spectral lenses table.

Reasoning:
- Filter `spectral_type` using `ILIKE` for near-infrared variants.

```sql
SELECT model_name, spectral_type, wavelength_min_nm, wavelength_max_nm,
       focus_length_mm, mount_raw
FROM spectral_lenses
WHERE spectral_type ILIKE '%NIR%';
```

---

**3. Wavelength Coverage Filter**

Natural Language:
Which spectral lenses cover the SWIR range up to 1700 nm?

Reasoning:
- Filter `wavelength_max_nm` for lenses with SWIR coverage for InGaAs sensor compatibility.

```sql
SELECT model_name, spectral_type, wavelength_min_nm, wavelength_max_nm, focus_length_mm
FROM spectral_lenses
WHERE wavelength_max_nm >= 1700;
```

---

**4. Wavelength Band Overlap Filter**

Natural Language:
Find spectral lenses that cover the 850 nm NIR wavelength.

Reasoning:
- Filter for lenses whose supported wavelength range includes 850 nm.

```sql
SELECT model_name, spectral_type, wavelength_min_nm, wavelength_max_nm, wavelength_raw
FROM spectral_lenses
WHERE wavelength_min_nm <= 850
  AND wavelength_max_nm >= 850;
```

---

**5. UV Lens Filter**

Natural Language:
List all spectral lenses that support UV wavelengths below 365 nm.

Reasoning:
- Filter `wavelength_min_nm` for lenses with UV capability, e.g., for fluorescence excitation or UV inspection.

```sql
SELECT model_name, spectral_type, wavelength_min_nm, wavelength_max_nm, focus_length_mm
FROM spectral_lenses
WHERE wavelength_min_nm <= 365;
```

---

**6. Aperture Filter**

Natural Language:
Find spectral lenses with a minimum F-number of 2.8 or lower for low-radiance spectral imaging.

Reasoning:
- Filter `f_no_min` for wide-aperture lenses that maximize light collection in dim spectral bands (e.g., SWIR, UV fluorescence).

```sql
SELECT model_name, f_no_min, f_no_raw, spectral_type, wavelength_min_nm, wavelength_max_nm
FROM spectral_lenses
WHERE f_no_min <= 2.8;
```

---

**7. Sensor Size and Wavelength Combined**

Natural Language:
Which spectral lenses support a maximum image size of at least 17 mm and cover NIR wavelengths?

Reasoning:
- Combine `max_image_size_value` and `wavelength_max_nm` filters for large-sensor NIR lenses.

```sql
SELECT model_name, spectral_type, max_image_size_value, wavelength_min_nm,
       wavelength_max_nm, focus_length_mm
FROM spectral_lenses
WHERE max_image_size_value >= 17
  AND wavelength_max_nm >= 900;
```

---

**8. Distortion and Spectral Type Combined**

Natural Language:
List hyperspectral lenses with TV distortion below 1%.

Reasoning:
- Combine `spectral_type` and `ABS(tv_distortion_percent)` filters; low distortion is critical in hyperspectral systems where spatial and spectral registration must be precise.

```sql
SELECT model_name, spectral_type, tv_distortion_percent, tv_distortion_operator,
       focus_length_mm
FROM spectral_lenses
WHERE spectral_type ILIKE '%hyper%'
  AND ABS(tv_distortion_percent) < 1;
```

---

## Notes

- **Primary Key:** `model_name`
- `spectral_type` is the primary categorical differentiator in this table; always filter on it first when the query specifies a spectral band (UV, NIR, SWIR, hyperspectral, broadband). Use `ILIKE` with `%` wildcards.
- `wavelength_min_nm` and `wavelength_max_nm` define the usable spectral transmission band; use a range-overlap query (`min <= target AND max >= target`) when filtering for a specific wavelength.
- Standard spectral band reference ranges: UV (200–400 nm), visible (400–700 nm), NIR (700–1100 nm), SWIR (1000–2500 nm). Hyperspectral lenses typically span a wide continuous range (e.g., 400–1000 nm).
- `tv_distortion_percent` may be positive or negative; always use `ABS()` for magnitude comparisons. `tv_distortion_operator` provides the inequality context.
- `flange_distance` must be verified against the target camera body's flange focal distance, especially for non-standard sensors (SWIR InGaAs, UV-enhanced CMOS) which may use non-standard camera bodies.
- `size_length_min_mm` and `size_length_max_mm` represent the physical body length range.
- All `*_raw`, `mount_raw`, and `spectral_type` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "spectral lens", "NIR lens", "SWIR lens", "UV lens", "hyperspectral lens", "multispectral lens", "infrared lens", "broadband lens", "extended wavelength lens", or "InGaAs lens".

---
