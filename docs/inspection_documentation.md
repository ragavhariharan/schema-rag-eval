# Table: inspection_360_systems

## Purpose

Stores specifications for **360° inspection systems** — specialized optical assemblies designed to capture the complete circumferential surface of cylindrical or rotational objects in a single imaging pass, without rotating the object or camera. These systems use catadioptric (mirror + lens) or prismatic optical designs to redirect the image of an object's full outer (or inner) surface onto a single area scan camera sensor simultaneously. They are used for inspecting O-rings, vials, capsules, bottles, pins, connectors, fasteners, threads, and other cylindrical components in pharmaceutical, electronics, and precision manufacturing.

This table supports engineering lookups for selecting 360° systems by inspection type, working distance, measurable object diameter, inspection height, field of view, sensor size, illumination wavelength, and mount compatibility. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the inspection system model | text | Primary key. Used as the main lookup key across all queries. |
| inspection_type | Describes whether the system inspects the outer or inner surface of the object | text | E.g., "outer surface", "inner surface", "side surface". Use `ILIKE` for filtering. |
| list_price | Catalogue sales price of the system | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch". Use `ILIKE` for filtering. |
| max_image_size_raw | Raw text representation of the maximum supported image size | text | Original source string. Preserved for display. |
| max_image_size_value | Numeric extracted value of the maximum supported image size | numeric | Parsed dimension for filtering. Units typically mm or inches depending on source. |
| focus_length_mm | Focal length of the integrated lens component in millimeters | numeric | Units: mm. |
| lens_diameter_raw | Raw text describing the lens or prism assembly diameter | text | Original source string. Preserved for display. |
| lens_diameter_mm | Numeric diameter of the lens or prism assembly in millimeters | numeric | Units: mm. Relevant for housing and fixture clearance. |
| f_no_raw | Raw text representation of the F-number range | text | Original source string. Preserved for display. |
| f_no_min | Minimum (most open) F-number supported | numeric | Lower value = larger aperture = more light. |
| f_no_max | Maximum (most closed) F-number supported | numeric | Higher value = smaller aperture = greater depth of field. |
| fov_raw | Raw text describing the field of view | text | Original source string. Preserved for display. |
| fov_degrees | Total field of view in degrees | numeric | For 360° systems this is typically 360. Units: degrees. |
| wavelength_raw | Raw text describing the compatible illumination wavelength range | text | E.g., "visible", "400–700 nm". Use `ILIKE` for filtering. |
| wd_raw | Raw text representation of the working distance range | text | Original source string. Preserved for display. |
| wd_min_mm | Minimum working distance in millimeters | numeric | Closest operational distance from lens front to target surface. Units: mm. |
| wd_max_mm | Maximum working distance in millimeters | numeric | Farthest operational distance from lens front to target surface. Units: mm. |
| measurement_object_diameter_raw | Raw text describing the range of measurable object diameters | text | Original source string. Preserved for display. |
| measurement_object_diameter_min_mm | Minimum diameter of objects that can be inspected in millimeters | numeric | Objects smaller than this may fall outside the system's imaging range. Units: mm. |
| measurement_object_diameter_max_mm | Maximum diameter of objects that can be inspected in millimeters | numeric | Objects larger than this exceed the system's imaging envelope. Units: mm. |
| measurement_height_raw | Raw text describing the inspectable height range of the object | text | Original source string. Preserved for display. |
| measurement_height_min_mm | Minimum inspectable height of the object in millimeters | numeric | Units: mm. |
| measurement_height_max_mm | Maximum inspectable height of the object in millimeters | numeric | Units: mm. The axial extent of the 360° image captured in one shot. |
| inspection_mode | Describes the imaging mode or configuration | text | E.g., "reflective", "transmissive". Use `ILIKE` for filtering. |
| light_source_type | Type of integrated or recommended light source | text | E.g., "LED ring", "coaxial LED". Use `ILIKE` for filtering. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| flange_distance_mm | Distance from the camera mounting flange to the image sensor plane | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| size_raw | Raw text describing the physical dimensions of the system | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the system housing in millimeters | numeric | Units: mm. |
| size_length_mm | Length of the system housing in millimeters | numeric | Units: mm. |
| weight_g | Physical weight of the system in grams | numeric | Units: g. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `inspection_360_systems` is architecturally distinct from other lens tables due to its object-centric measurement columns (`measurement_object_diameter_*`, `measurement_height_*`).
* `mount_raw` and `max_image_size_value` can be cross-referenced with camera specifications to confirm sensor compatibility.
* `flange_distance_mm` can be used alongside camera flange distance specs to verify optical compatibility.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all 360° inspection systems with their inspection type, measurable object diameter range, and weight.

Reasoning:
- Select key system characterization columns.
- No filtering — return all rows.

```sql
SELECT model_name, inspection_type, measurement_object_diameter_min_mm,
       measurement_object_diameter_max_mm, weight_g
FROM inspection_360_systems;
```

---

**2. Object Diameter Compatibility**

Natural Language:
Which 360° inspection systems can inspect objects with a diameter of 10 mm?

Reasoning:
- Filter systems where the target diameter (10 mm) falls within the measurable diameter range.

```sql
SELECT model_name, measurement_object_diameter_min_mm, measurement_object_diameter_max_mm,
       inspection_type
FROM inspection_360_systems
WHERE measurement_object_diameter_min_mm <= 10
  AND measurement_object_diameter_max_mm >= 10;
```

---

**3. Inspection Height Filter**

Natural Language:
Find 360° systems that can inspect an object height of at least 20 mm in a single shot.

Reasoning:
- Filter `measurement_height_max_mm` for systems with tall enough imaging envelopes.

```sql
SELECT model_name, measurement_height_min_mm, measurement_height_max_mm, inspection_type
FROM inspection_360_systems
WHERE measurement_height_max_mm >= 20;
```

---

**4. Outer Surface Inspection Filter**

Natural Language:
List all systems designed for outer surface inspection.

Reasoning:
- Filter `inspection_type` for outer surface variants using `ILIKE`.

```sql
SELECT model_name, inspection_type, measurement_object_diameter_min_mm,
       measurement_object_diameter_max_mm
FROM inspection_360_systems
WHERE inspection_type ILIKE '%outer%';
```

---

**5. Mount and Sensor Compatibility**

Natural Language:
Which 360° systems use a C-mount and support a maximum image size of at least 10 mm?

Reasoning:
- Filter `mount_raw` and `max_image_size_value` for camera compatibility.

```sql
SELECT model_name, mount_raw, max_image_size_value, max_image_size_raw
FROM inspection_360_systems
WHERE mount_raw ILIKE '%C%'
  AND max_image_size_value >= 10;
```

---

**6. Working Distance Filter**

Natural Language:
Find 360° inspection systems with a maximum working distance greater than 50 mm.

Reasoning:
- Filter `wd_max_mm` for systems usable at longer standoff distances.

```sql
SELECT model_name, wd_min_mm, wd_max_mm, inspection_type
FROM inspection_360_systems
WHERE wd_max_mm > 50;
```

---

**7. Light Source Filter**

Natural Language:
Which systems include an integrated LED light source?

Reasoning:
- Filter `light_source_type` for LED-based illumination using `ILIKE`.

```sql
SELECT model_name, light_source_type, inspection_type, inspection_mode
FROM inspection_360_systems
WHERE light_source_type ILIKE '%LED%';
```

---

## Notes

- **Primary Key:** `model_name`
- `measurement_object_diameter_min_mm` and `measurement_object_diameter_max_mm` define the physical range of object diameters the system can image; always check that the target object diameter falls within this range.
- `measurement_height_max_mm` is the maximum axial height of the object's circumferential surface captured in a single exposure — critical for determining if one shot suffices or multiple passes are needed.
- `inspection_type` distinguishes outer surface (most common), inner surface (bore inspection), and other variants.
- `fov_degrees` is typically 360 for these systems, but verify with `fov_raw` for systems with partial coverage.
- `flange_distance_mm` is camera-side clearance; verify against the target camera's flange focal distance.
- All `*_raw` fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "360 inspection", "circumferential inspection", "cylindrical surface imaging", "all-around inspection", "side surface inspection", "360-degree lens", "bottle inspection", or "pin inspection".

---
