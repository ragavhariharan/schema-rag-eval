# Table: autofocus_lenses

## Purpose

Stores specifications for **autofocus lenses** — motorized machine vision lenses with integrated autofocus mechanisms driven by stepper motors or other actuators. These lenses are used in automated inspection systems, smart cameras, and robotic vision platforms where dynamic refocusing is required without manual intervention — such as inspecting objects at variable distances on a production line, multi-distance measurement tasks, or adaptive focus control in embedded systems.

This table captures both the optical characteristics (focal length, aperture, field of view, working distance, distortion) and the electromechanical drive parameters (motor type, step angle, speed, precision, response time, communication method, and excitation/drive modes) needed to fully integrate and program an autofocus lens into a control system. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the lens model | text | Primary key. Used as the main lookup key across all queries. |
| focus_length_mm | Focal length of the lens in millimeters | numeric | Units: mm. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| tv_distortion_operator | Comparison operator for TV distortion value | text | E.g., "<", "≤". Provides inequality context for `tv_distortion_percent`. |
| tv_distortion_percent | TV distortion magnitude as a percentage | numeric | Negative = barrel distortion; positive = pincushion. Use `ABS()` for magnitude comparisons. |
| mod_raw | Raw text for the Minimum Object Distance specification | text | Original source string. Preserved for display. |
| mod_distance_m | Minimum object distance in meters | numeric | Closest distance at which the lens can achieve focus. Units: m. |
| mod_magnification | Optical magnification at the minimum object distance | numeric | Dimensionless ratio. |
| magnification_raw | Raw text representation of the magnification range | text | Original source string. Preserved for display. |
| magnification_min | Minimum optical magnification ratio | numeric | Dimensionless. Smaller = wider coverage. |
| magnification_max | Maximum optical magnification ratio | numeric | Dimensionless. Larger = more zoomed-in coverage. |
| object_image_distance_raw | Raw text for the object-to-image distance specification | text | Original source string. Preserved for display. |
| object_image_distance_min_mm | Minimum total object-to-image (conjugate) distance in millimeters | numeric | Units: mm. Used in optical path planning. |
| object_image_distance_max_mm | Maximum total object-to-image distance in millimeters | numeric | Units: mm. |
| wd_raw | Raw text representation of the working distance range | text | Original source string. Preserved for display. |
| wd_min_mm | Minimum working distance in millimeters | numeric | Closest operational distance from lens front to target. Units: mm. |
| wd_max_mm | Maximum working distance in millimeters | numeric | Farthest operational distance from lens front to target. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount". Use `ILIKE` for filtering. |
| filter_thread_raw | Raw text describing the filter thread size | text | E.g., "M43×0.75". Use `ILIKE` for matching. |
| voltage_raw | Raw text describing the operating voltage | text | E.g., "5V DC". Use `ILIKE` for filtering. |
| communication_method | Protocol or interface used for autofocus control communication | text | E.g., "RS-232", "USB", "I2C". Use `ILIKE` for filtering. |
| speed_range_raw | Raw text describing the motor speed range | text | Original source string. Preserved for display. |
| speed_min_rpm | Minimum motor speed in revolutions per minute | numeric | Units: RPM. |
| speed_max_rpm | Maximum motor speed in revolutions per minute | numeric | Units: RPM. |
| motion_precision_raw | Raw text describing the motion precision specification | text | Original source string. Preserved for display. |
| motion_precision_degree | Motion precision expressed in degrees | numeric | Smaller value = finer positional accuracy. Units: degrees. |
| response_time_raw | Raw text describing the autofocus response time | text | Original source string. Preserved for display. |
| response_time_ms | Autofocus response time in milliseconds | numeric | Time from trigger to focused image. Lower = faster. Units: ms. |
| controller_raw | Raw text describing the required or compatible motor controller | text | E.g., controller model or type. Use `ILIKE` for filtering. |
| motor_type | Type of motor used in the autofocus mechanism | text | E.g., "stepper motor", "piezo". Use `ILIKE` for filtering. |
| driving_voltage_raw | Raw text describing the motor driving voltage | text | May differ from system voltage. Preserved for display. |
| excitation_mode | Electrical excitation mode of the motor | text | E.g., "2-phase", "1-2 phase". Determines torque/speed characteristics. |
| drive_mode | Motor drive mode | text | E.g., "full step", "half step", "micro step". Affects resolution and smoothness. |
| step_angle_raw | Raw text describing the motor step angle | text | Original source string. Preserved for display. |
| step_angle_degree | Motor step angle in degrees per step | numeric | Smaller step angle = finer focus resolution. Units: degrees/step. |
| reduction_ratio_raw | Raw text describing the gear reduction ratio of the drive mechanism | text | E.g., "1:10". Affects torque multiplication and speed reduction. |
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

* `autofocus_lenses` ↔ `large_format_autofocus_lenses`: both tables share autofocus drive parameters (`communication_method`, `speed_min_rpm`, `speed_max_rpm`, `motion_precision_degree`, `response_time_ms`, `controller_raw`) and can be compared for autofocus performance.
* Shares common optical columns with `fa_lenses`, `anti_vibration_lenses`, `large_format_lenses` for cross-family optical comparisons.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all autofocus lenses with their focal length, working distance range, and response time.

Reasoning:
- Select key optical and electromechanical performance columns.
- No filtering — return all rows.

```sql
SELECT model_name, focus_length_mm, wd_min_mm, wd_max_mm, response_time_ms
FROM autofocus_lenses;
```

---

**2. Response Time Filter**

Natural Language:
Find all autofocus lenses with a response time under 100 milliseconds.

Reasoning:
- Filter `response_time_ms` for fast-responding lenses suited to high-throughput inspection.

```sql
SELECT model_name, response_time_ms, response_time_raw, focus_length_mm
FROM autofocus_lenses
WHERE response_time_ms < 100;
```

---

**3. Motor Type Filter**

Natural Language:
Which autofocus lenses use a stepper motor?

Reasoning:
- Filter `motor_type` for stepper motor variants using `ILIKE`.

```sql
SELECT model_name, motor_type, step_angle_degree, drive_mode, focus_length_mm
FROM autofocus_lenses
WHERE motor_type ILIKE '%stepper%';
```

---

**4. Communication Method Filter**

Natural Language:
List all autofocus lenses that support RS-232 communication.

Reasoning:
- Filter `communication_method` for RS-232 compatible lenses.

```sql
SELECT model_name, communication_method, controller_raw, focus_length_mm
FROM autofocus_lenses
WHERE communication_method ILIKE '%RS-232%';
```

---

**5. Motion Precision Filter**

Natural Language:
Find autofocus lenses with a motion precision of 0.1 degrees or finer.

Reasoning:
- Filter `motion_precision_degree` for lenses with high positional accuracy.

```sql
SELECT model_name, motion_precision_degree, motion_precision_raw, step_angle_degree
FROM autofocus_lenses
WHERE motion_precision_degree <= 0.1;
```

---

**6. Aperture and Working Distance Combined Filter**

Natural Language:
Which autofocus lenses have a minimum F-number of 2.8 or lower and a maximum working distance of at least 300 mm?

Reasoning:
- Combine `f_no_min` and `wd_max_mm` filters for fast lenses with long reach.

```sql
SELECT model_name, f_no_min, wd_max_mm, focus_length_mm
FROM autofocus_lenses
WHERE f_no_min <= 2.8
  AND wd_max_mm >= 300;
```

---

**7. Drive Mode Filter**

Natural Language:
List autofocus lenses that support half-step drive mode.

Reasoning:
- Filter `drive_mode` for half-step operation, which balances resolution and torque.

```sql
SELECT model_name, drive_mode, step_angle_degree, motor_type
FROM autofocus_lenses
WHERE drive_mode ILIKE '%half%';
```

---

## Notes

- **Primary Key:** `model_name`
- `tv_distortion_percent` may be positive or negative; use `ABS()` for magnitude-only comparisons. `tv_distortion_operator` provides the inequality context.
- `response_time_ms` is a key differentiator for high-speed production line applications; lower is faster.
- `motion_precision_degree` and `step_angle_degree` are both in degrees; `step_angle_degree` is the raw motor step resolution, while `motion_precision_degree` reflects the effective positioning accuracy after gearing.
- `reduction_ratio_raw` is stored as text (e.g., "1:10"); parse numerically if ratio-based calculations are needed.
- All `*_raw` text columns should be queried with `ILIKE` and `%` wildcards.
- Three FOV angle column sets (`angle_primary_*`, `angle_secondary_*`, `angle_tertiary_*`) accommodate multiple sensor size configurations.
- This table is optimized for RAG chunk retrieval when queries mention "autofocus lens", "motorized focus", "stepper motor lens", "auto focus control", "focus response time", or "motorized zoom".

---
