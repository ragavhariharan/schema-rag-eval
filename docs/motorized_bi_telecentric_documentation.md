# Table: motorized_bi_telecentric_lenses

## Purpose

Stores specifications for **motorized bi-telecentric lenses** — precision optical systems combining the geometric measurement advantages of bilateral telecentricity with an integrated motorized focus drive. Bi-telecentric (or double-telecentric) lenses maintain constant magnification and eliminate parallax error across the depth of field on both the object side and the image side simultaneously. This property makes them the preferred choice for non-contact dimensional measurement, gauging, and precision metrology in semiconductor inspection, LCD glass edge measurement, connector and O-ring dimensional QC, precision machined part inspection, and any application where sub-pixel measurement accuracy is required.

The motorized variant adds programmable, automated focus control via a drive motor, enabling dynamic refocusing without disturbing the optical alignment or magnification — critical in inline measurement systems where the object height varies or in multi-focus Z-stack acquisition.

This table captures both the optical metrological specifications (magnification, numerical aperture, telecentricity, distortion, relative illuminance, TTL) and the electromechanical drive parameters (speed, precision, response time, communication method, controller, voltage) needed for full system integration. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| illumination_type | Type of illumination the lens is designed to work with | text | E.g., "coaxial", "darkfield", "brightfield". Bi-telecentric lenses require telecentric illumination to preserve measurement accuracy. Use `ILIKE` for filtering. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| magnification_raw | Raw text representation of the magnification value or range | text | Original source string (e.g., "0.5×", "1× – 2×"). Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. Smaller = wider coverage at a given sensor size. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. Larger = higher resolution per pixel. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| wd_raw | Raw text representation of the working distance | text | Original source string. Preserved for display. |
| wd_mm | Working distance from lens front element to object surface | numeric | Fixed working distance for telecentric lenses. Units: mm. Telecentricity is only valid near this distance. |
| numerical_aperture | Numerical aperture on the object side | numeric | Dimensionless. Determines resolution and depth of field. Higher NA = better resolution but shallower DOF. |
| telecentricity_raw | Raw text describing the telecentricity specification | text | Original source string (e.g., "< 0.1°"). Preserved for display. |
| telecentricity_degrees | Telecentricity angular error in degrees | numeric | Maximum deviation of the chief ray from true telecentric (0° = perfect telecentricity). Lower = more accurate measurement. Units: degrees. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel; positive = pincushion. Use `ABS()` for magnitude comparisons. Telecentric measurement lenses are engineered for extremely low distortion. |
| relative_illuminance_operator | Comparison operator for relative illuminance value | text | E.g., "≥", ">". Provides inequality context for `relative_illuminance_percent`. |
| relative_illuminance_percent | Relative illuminance at the image periphery as a percentage of the center | numeric | Higher = more uniform measurement illumination. Critical for edge detection accuracy. |
| ttl_mm | Total track length of the lens system in millimeters | numeric | End-to-end physical length from the front of the lens to the image sensor plane. Determines minimum housing depth. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| voltage_raw | Raw text describing the operating voltage of the motor drive | text | E.g., "5V DC", "12V DC". Use `ILIKE` for filtering. |
| communication_method | Protocol or interface used for motor control communication | text | E.g., "RS-232", "USB". Use `ILIKE` for filtering. |
| speed_range_raw | Raw text describing the motor speed range | text | Original source string. Preserved for display. |
| speed_min_rpm | Minimum motor speed in revolutions per minute | numeric | Units: RPM. |
| speed_max_rpm | Maximum motor speed in revolutions per minute | numeric | Units: RPM. |
| motion_precision_raw | Raw text describing the motion precision specification | text | Original source string. Preserved for display. |
| motion_precision_degree | Motion precision expressed in degrees | numeric | Smaller = finer focus positioning. Units: degrees. |
| response_time_raw | Raw text describing the motor response time | text | Original source string. Preserved for display. |
| response_time_operator | Comparison operator for the response time value | text | E.g., "<", "≤". Provides inequality context for `response_time_ms`. |
| response_time_ms | Motor response time in milliseconds | numeric | Time from trigger to completed focus movement. Lower = faster. Units: ms. |
| controller_raw | Raw text describing the required or compatible motor controller | text | Use `ILIKE` for filtering. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `motorized_bi_telecentric_lenses` ↔ `autofocus_lenses`, `large_format_autofocus_lenses`: all three tables share motorized drive parameter columns (`communication_method`, `speed_min_rpm`, `speed_max_rpm`, `motion_precision_degree`, `response_time_ms`, `controller_raw`) for cross-family autofocus performance comparisons.
* `motorized_bi_telecentric_lenses` ↔ `macro_lenses`: both cover precision high-magnification imaging; telecentric lenses add parallax-free measurement capability that macro lenses lack.
* `numerical_aperture` is shared conceptually with `microscope_lenses.numerical_aperture` for resolution comparisons between microscope objectives and telecentric measurement lenses.
* `telecentricity_degrees` is unique to this table and its non-motorized counterpart tables (bi-telecentric and mono-telecentric families).

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all motorized bi-telecentric lenses with their magnification, working distance, numerical aperture, and telecentricity.

Reasoning:
- Select the key metrological and identification columns.
- No filtering — return all rows.

```sql
SELECT model_name, magnification_min, magnification_max, wd_mm,
       numerical_aperture, telecentricity_degrees
FROM motorized_bi_telecentric_lenses;
```

---

**2. Telecentricity Filter**

Natural Language:
Find all motorized bi-telecentric lenses with a telecentricity error below 0.1 degrees for high-accuracy measurement.

Reasoning:
- Filter `telecentricity_degrees` for the most precise telecentric performance.

```sql
SELECT model_name, telecentricity_degrees, telecentricity_raw, magnification_max, wd_mm
FROM motorized_bi_telecentric_lenses
WHERE telecentricity_degrees < 0.1;
```

---

**3. Numerical Aperture Filter**

Natural Language:
Which motorized bi-telecentric lenses have a numerical aperture of 0.07 or higher?

Reasoning:
- Filter `numerical_aperture` for higher-NA lenses with finer object-side resolution.

```sql
SELECT model_name, numerical_aperture, magnification_max, wd_mm, telecentricity_degrees
FROM motorized_bi_telecentric_lenses
WHERE numerical_aperture >= 0.07;
```

---

**4. Distortion Filter**

Natural Language:
List motorized bi-telecentric lenses with TV distortion below 0.1% for precision dimensional measurement.

Reasoning:
- Use `ABS()` to handle signed distortion. Telecentric measurement lenses should have very low distortion.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, magnification_max
FROM motorized_bi_telecentric_lenses
WHERE ABS(tv_distortion_percent) < 0.1;
```

---

**5. Relative Illuminance Filter**

Natural Language:
Find motorized bi-telecentric lenses with relative illuminance of 80% or higher for uniform edge detection.

Reasoning:
- Filter `relative_illuminance_percent` for lenses with consistent brightness across the measurement field.

```sql
SELECT model_name, relative_illuminance_percent, relative_illuminance_operator,
       magnification_max, wd_mm
FROM motorized_bi_telecentric_lenses
WHERE relative_illuminance_percent >= 80;
```

---

**6. Response Time Filter**

Natural Language:
Which motorized bi-telecentric lenses have a motor response time of 150 ms or less?

Reasoning:
- Filter `response_time_ms` for fast focus repositioning suitable for high-throughput inline measurement.

```sql
SELECT model_name, response_time_ms, response_time_raw, response_time_operator,
       communication_method
FROM motorized_bi_telecentric_lenses
WHERE response_time_ms <= 150;
```

---

**7. Communication Method and Magnification Combined**

Natural Language:
List motorized bi-telecentric lenses that support RS-232 control and have a magnification of 1× or higher.

Reasoning:
- Combine `communication_method` and `magnification_max` filters for RS-232 controlled high-magnification telecentric lenses.

```sql
SELECT model_name, communication_method, magnification_min, magnification_max, wd_mm
FROM motorized_bi_telecentric_lenses
WHERE communication_method ILIKE '%RS-232%'
  AND magnification_max >= 1.0;
```

---

**8. TTL Length Filter**

Natural Language:
Find motorized bi-telecentric lenses with a total track length under 250 mm for compact system integration.

Reasoning:
- Filter `ttl_mm` for lenses with shorter physical housing requirements.

```sql
SELECT model_name, ttl_mm, magnification_max, wd_mm, mount_raw
FROM motorized_bi_telecentric_lenses
WHERE ttl_mm < 250;
```

---

## Notes

- **Primary Key:** `model_name`
- `telecentricity_degrees` is the defining metric of this lens family: lower values indicate more precise telecentric geometry, directly translating to lower parallax-induced measurement error. Sub-0.1° is considered high-precision telecentric performance.
- `tv_distortion_percent` in telecentric lenses is typically engineered to extremely low values (< 0.1%); use `ABS()` for magnitude comparisons.
- `wd_mm` is a fixed value for telecentric lenses — the telecentric property is only preserved at or near this design working distance. Operating outside this distance degrades telecentricity.
- `ttl_mm` (total track length) is the full end-to-end physical length of the optical system; critical for system housing design and must be accounted for when planning camera-to-lens-to-object distances.
- `relative_illuminance_percent` directly affects edge detection uniformity in measurement applications: low peripheral illuminance causes inconsistent edge contrast and measurement error.
- `illumination_type` is especially important for bi-telecentric lenses: they require telecentric illumination (typically coaxial or diffuse backlight) to fully realize their parallax-free measurement advantage.
- `response_time_operator` provides the inequality context for `response_time_ms`.
- All `*_raw` and `mount_raw` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "bi-telecentric lens", "double telecentric", "telecentric measurement lens", "motorized telecentric", "non-contact measurement lens", "parallax-free lens", "dimensional gauging lens", or "telecentric with autofocus".

---
