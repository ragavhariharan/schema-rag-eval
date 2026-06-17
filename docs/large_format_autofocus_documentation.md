# Table: large_format_autofocus_lenses

## Purpose

Stores specifications for **large format autofocus lenses** — motorized lenses designed for large image circle sensors (typically greater than 1 inch diagonal) combined with integrated autofocus drive mechanisms. These lenses serve applications demanding both wide sensor coverage and automated, programmable focus control — such as multi-megapixel flat panel display inspection, large-area PCB inspection, semiconductor wafer metrology, and precision measurement systems where the sensor size exceeds what standard C-mount FA lenses can cover.

This table captures both optical characteristics (focal length, aperture, magnification range, sensor coverage, distortion, flange distance) and electromechanical autofocus parameters (speed, motion precision, response time, communication method, controller) needed for full integration. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| max_image_size_raw | Raw text representation of the maximum supported image (sensor) size | text | Original source string (e.g., "1.1 inch", "43.3 mm"). Preserved for display. |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed dimension for filtering. Units: mm or inches depending on source context. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel distortion; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M95×1.0". Use `ILIKE` for matching. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string. Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. Smaller = wider coverage. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. Larger = more zoomed-in coverage. |
| standard_magnification | Standard or nominal magnification label for this lens | text | May include "×" suffix or descriptive labels. Use `ILIKE` for matching. |
| wd_mm | Working distance from lens front element to object surface | numeric | Fixed working distance value. Units: mm. |
| flange_distance | Distance from camera mounting flange to image sensor plane | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "F-mount", "M72". Use `ILIKE` for filtering. |
| voltage_raw | Raw text describing the operating voltage of the autofocus drive | text | E.g., "5V DC", "12V DC". Use `ILIKE` for filtering. |
| communication_method | Protocol or interface used for autofocus control communication | text | E.g., "RS-232", "USB". Use `ILIKE` for filtering. |
| speed_range_raw | Raw text describing the motor speed range | text | Original source string. Preserved for display. |
| speed_min_rpm | Minimum motor speed in revolutions per minute | numeric | Units: RPM. |
| speed_max_rpm | Maximum motor speed in revolutions per minute | numeric | Units: RPM. |
| motion_precision_raw | Raw text describing the motion precision specification | text | Original source string. Preserved for display. |
| motion_precision_degree | Motion precision expressed in degrees | numeric | Smaller value = finer positional accuracy. Units: degrees. |
| response_time_raw | Raw text describing the autofocus response time | text | Original source string. Preserved for display. |
| response_time_operator | Comparison operator for the response time value | text | E.g., "<", "≤". Provides inequality context for `response_time_ms`. |
| response_time_ms | Autofocus response time in milliseconds | numeric | Time from trigger to focused image. Lower = faster. Units: ms. |
| controller_raw | Raw text describing the required or compatible motor controller | text | Use `ILIKE` for filtering. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_min_mm | Minimum physical length of the lens body in millimeters | numeric | Units: mm. |
| size_length_max_mm | Maximum physical length of the lens body in millimeters | numeric | Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `large_format_autofocus_lenses` ↔ `large_format_lenses`: both tables cover large sensor formats and share optical specification columns; `large_format_autofocus_lenses` adds motor-drive columns absent in the static variant.
* `large_format_autofocus_lenses` ↔ `autofocus_lenses`: both share autofocus drive parameter columns (`communication_method`, `speed_min_rpm`, `speed_max_rpm`, `motion_precision_degree`, `response_time_ms`, `controller_raw`) and can be cross-compared for drive performance.
* `max_image_size_value` can be cross-referenced with camera sensor diagonal specifications to verify coverage.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all large format autofocus lenses with their focal length, maximum image size, and working distance.

Reasoning:
- Select identifying and key optical specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, focus_length_mm, max_image_size_value, max_image_size_raw, wd_mm
FROM large_format_autofocus_lenses;
```

---

**2. Sensor Size Filter**

Natural Language:
Find all large format autofocus lenses that support a maximum image size of at least 43 mm.

Reasoning:
- Filter `max_image_size_value` for lenses covering large sensor formats.

```sql
SELECT model_name, max_image_size_value, max_image_size_raw, focus_length_mm
FROM large_format_autofocus_lenses
WHERE max_image_size_value >= 43;
```

---

**3. Response Time Filter**

Natural Language:
Which large format autofocus lenses have a response time of 200 ms or less?

Reasoning:
- Filter `response_time_ms` for fast autofocus performance.

```sql
SELECT model_name, response_time_ms, response_time_raw, response_time_operator
FROM large_format_autofocus_lenses
WHERE response_time_ms <= 200;
```

---

**4. Communication Method Filter**

Natural Language:
List all large format autofocus lenses that support RS-232 communication.

Reasoning:
- Filter `communication_method` using `ILIKE`.

```sql
SELECT model_name, communication_method, controller_raw, focus_length_mm
FROM large_format_autofocus_lenses
WHERE communication_method ILIKE '%RS-232%';
```

---

**5. Distortion Filter**

Natural Language:
Find large format autofocus lenses with TV distortion under 1%.

Reasoning:
- Use `ABS()` to handle signed distortion values.

```sql
SELECT model_name, tv_distortion_percent, tv_distortion_operator, focus_length_mm
FROM large_format_autofocus_lenses
WHERE ABS(tv_distortion_percent) < 1;
```

---

**6. Magnification Range Filter**

Natural Language:
Which large format autofocus lenses support magnification values between 0.1× and 0.5×?

Reasoning:
- Filter where the desired magnification range overlaps with the lens magnification range.

```sql
SELECT model_name, magnification_min, magnification_max, standard_magnification
FROM large_format_autofocus_lenses
WHERE magnification_min <= 0.5
  AND magnification_max >= 0.1;
```

---

**7. Motor Speed Filter**

Natural Language:
List large format autofocus lenses with a maximum motor speed exceeding 500 RPM.

Reasoning:
- Filter `speed_max_rpm` for high-speed focus drive applications.

```sql
SELECT model_name, speed_min_rpm, speed_max_rpm, speed_range_raw
FROM large_format_autofocus_lenses
WHERE speed_max_rpm > 500;
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive or negative; use `ABS()` for magnitude comparisons. `tv_distortion_operator` gives the inequality context.
- `response_time_operator` provides the inequality context for `response_time_ms` (e.g., "≤ 150 ms").
- `wd_mm` is a single fixed value (not a range), reflecting these lenses' fixed working distance design.
- `flange_distance` is distinct from `wd_mm`: it is the camera-side optical distance, not the object-side clearance.
- `size_length_min_mm` and `size_length_max_mm` represent the physical body length range across the autofocus travel.
- All `*_raw` and `mount_raw` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "large format autofocus", "large sensor autofocus lens", "motorized large format", "large image circle autofocus", or "big sensor auto focus lens".

---
