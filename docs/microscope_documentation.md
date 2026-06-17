# Table: microscope_lenses

## Purpose

Stores specifications for **microscope lenses** — high-magnification optical systems used in digital microscopy, video microscopy, and machine vision microscopy for imaging fine structures, biological specimens, semiconductor features, MEMS devices, surface defects at the micron scale, and other targets requiring resolution beyond the capability of standard macro or FA lenses. This table covers both the **objective lens** (the high-power element closest to the specimen) and the **tube lens** (the relay element that projects the objective's intermediate image onto the camera sensor), as well as complete integrated microscope lens systems.

Microscope lenses are characterized not only by magnification but also by numerical aperture (NA), depth of field (DOF), object resolution, tube length compatibility, illumination type, and spectral wavelength range. This table supports engineering lookups across all of these parameters and enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the microscope lens or system model | text | Primary key. Used as the main lookup key across all queries. |
| microscope_type | Describes the microscope optical configuration | text | E.g., "infinity corrected", "finite conjugate", "stereo". Use `ILIKE` for filtering. |
| list_price | Catalogue sales price of the lens or system | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| illumination_type | Type of illumination the lens is designed to work with | text | E.g., "brightfield", "darkfield", "coaxial", "transmitted", "reflected". Use `ILIKE` for filtering. |
| focus_length_mm | Focal length of the lens or tube lens component in millimeters | numeric | For infinity-corrected systems, this is typically the tube lens focal length. Units: mm. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/1.8 inch", "2/3 inch". Use `ILIKE` for filtering. |
| magnification_raw | Raw text representation of the magnification value or range | text | Original source string (e.g., "10×", "5× – 50×"). Preserved for display. |
| magnification_min | Minimum optical magnification ratio supported | numeric | Dimensionless. E.g., 5 = 5× magnification. |
| magnification_max | Maximum optical magnification ratio supported | numeric | Dimensionless. Higher values = finer detail imaging. |
| wd_mm | Working distance from the front lens element to the specimen surface | numeric | Critical for stage clearance. Very short in high-NA objectives (< 1 mm). Units: mm. |
| numerical_aperture | Numerical aperture of the objective lens | numeric | Dimensionless. Higher NA = better resolution and light collection but shallower DOF. Key specification for diffraction-limited resolution. |
| object_resolution_raw | Raw text describing the minimum resolvable feature size | text | Original source string (e.g., "< 1 µm"). Preserved for display. |
| object_resolution_um | Minimum resolvable object feature size in micrometers | numeric | Smaller value = finer resolution. Units: µm. Determined by NA and wavelength. |
| dof_raw | Raw text describing the depth of field | text | Original source string (e.g., "± 2 µm"). Preserved for display. |
| dof_um | Depth of field in micrometers | numeric | Axial range within which objects remain acceptably sharp. Units: µm. Smaller DOF at higher NA and magnification. |
| wavelength_raw | Raw text describing the supported illumination wavelength range | text | Original source string. Preserved for display. |
| wavelength_min_nm | Minimum supported wavelength in nanometers | numeric | Lower bound of the usable spectral range. Units: nm. |
| wavelength_max_nm | Maximum supported wavelength in nanometers | numeric | Upper bound of the usable spectral range. Units: nm. |
| objective_mount_raw | Raw text describing the objective lens thread or mount standard | text | E.g., "RMS", "M25×0.75", "M32×0.75". Use `ILIKE` for filtering. |
| tube_lens_mount_raw | Raw text describing the tube lens mount standard | text | E.g., "M42×1.0", "Leica", "Nikon". Use `ILIKE` for filtering. |
| tube_length_mm | Mechanical tube length for finite-conjugate systems, or reference tube length for infinity systems | numeric | Standard values: 160 mm (finite DIN), 200 mm (Nikon), 180 mm (Olympus), 165 mm (Leica). Units: mm. |
| flange_distance | Distance from camera mounting flange to image sensor plane | numeric | Used to confirm physical compatibility with camera body. Units: mm. |
| mount_raw | Raw text describing the camera mount type | text | E.g., "C-mount", "F-mount". Use `ILIKE` for filtering. |
| angle_primary_raw | Raw text for the primary FOV angle specification | text | Original source string. Preserved for display. |
| angle_primary_h | Horizontal component of the primary FOV angle | numeric | Units: degrees. |
| angle_primary_v | Vertical component of the primary FOV angle | numeric | Units: degrees. |
| angle_secondary_raw | Raw text for the secondary FOV angle specification | text | FOV at a different sensor size or configuration. |
| angle_secondary_h | Horizontal component of the secondary FOV angle | numeric | Units: degrees. |
| angle_secondary_v | Vertical component of the secondary FOV angle | numeric | Units: degrees. |
| angle_tertiary_raw | Raw text for the tertiary FOV angle specification | text | FOV at a third sensor size or configuration. |
| angle_tertiary_h | Horizontal component of the tertiary FOV angle | numeric | Units: degrees. |
| angle_tertiary_v | Vertical component of the tertiary FOV angle | numeric | Units: degrees. |
| angle_quaternary_raw | Raw text for the quaternary FOV angle specification | text | FOV at a fourth sensor size or configuration. Unique to this table. |
| angle_quaternary_h | Horizontal component of the quaternary FOV angle | numeric | Units: degrees. |
| angle_quaternary_v | Vertical component of the quaternary FOV angle | numeric | Units: degrees. |
| size_raw | Raw text describing the physical dimensions of the lens | text | Original source string. Preserved for display. |
| size_diameter_mm | Outer diameter of the lens body in millimeters | numeric | Units: mm. |
| size_length_mm | Physical length of the lens body in millimeters | numeric | Units: mm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `microscope_lenses` ↔ `macro_lenses`: both serve high-magnification imaging; microscope lenses extend into higher magnification ranges (10×–200×+) and are characterized by NA rather than just F-number.
* `microscope_lenses` ↔ `magnifying_lenses`: magnifying lenses cover lower magnification ranges that overlap with the lower end of microscope objectives.
* `objective_mount_raw` and `tube_lens_mount_raw` define the internal optical coupling standard; these are distinct from `mount_raw` (camera side).
* `wavelength_min_nm` / `wavelength_max_nm` are shared with `magnifying_lenses` and `spectral_lenses` for spectral compatibility cross-referencing.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all microscope lenses with their magnification range, numerical aperture, and working distance.

Reasoning:
- Select the most diagnostically useful specification columns for microscope lens selection.
- No filtering — return all rows.

```sql
SELECT model_name, magnification_min, magnification_max, numerical_aperture, wd_mm
FROM microscope_lenses;
```

---

**2. Numerical Aperture Filter**

Natural Language:
Find all microscope lenses with a numerical aperture of 0.5 or higher for high-resolution imaging.

Reasoning:
- Filter `numerical_aperture` for high-NA objectives that provide finer diffraction-limited resolution.

```sql
SELECT model_name, numerical_aperture, object_resolution_um, wd_mm, magnification_max
FROM microscope_lenses
WHERE numerical_aperture >= 0.5;
```

---

**3. Object Resolution Filter**

Natural Language:
Which microscope lenses can resolve features smaller than 1 micrometer?

Reasoning:
- Filter `object_resolution_um` for sub-micron resolving power.

```sql
SELECT model_name, object_resolution_um, object_resolution_raw, numerical_aperture,
       magnification_max
FROM microscope_lenses
WHERE object_resolution_um < 1;
```

---

**4. Working Distance Filter**

Natural Language:
Find microscope lenses with a working distance greater than 10 mm for long-distance objectives.

Reasoning:
- Filter `wd_mm` for long working distance (LWD) objectives that allow clearance for covers, slides, or sample handling.

```sql
SELECT model_name, wd_mm, numerical_aperture, magnification_max, microscope_type
FROM microscope_lenses
WHERE wd_mm > 10;
```

---

**5. Depth of Field Filter**

Natural Language:
List microscope lenses with a depth of field greater than 10 micrometers for imaging rough or uneven surfaces.

Reasoning:
- Filter `dof_um` for lenses with large DOF suitable for non-flat specimens.

```sql
SELECT model_name, dof_um, dof_raw, magnification_max, numerical_aperture
FROM microscope_lenses
WHERE dof_um > 10;
```

---

**6. Illumination Type Filter**

Natural Language:
Which microscope lenses are designed for darkfield illumination?

Reasoning:
- Filter `illumination_type` using `ILIKE` for darkfield-compatible lenses.

```sql
SELECT model_name, illumination_type, numerical_aperture, magnification_max, wd_mm
FROM microscope_lenses
WHERE illumination_type ILIKE '%darkfield%';
```

---

**7. Wavelength Range Filter**

Natural Language:
Find microscope lenses that support UV wavelengths down to 350 nm.

Reasoning:
- Filter `wavelength_min_nm` for UV-capable objectives used in fluorescence or UV inspection.

```sql
SELECT model_name, wavelength_min_nm, wavelength_max_nm, wavelength_raw, magnification_max
FROM microscope_lenses
WHERE wavelength_min_nm <= 350;
```

---

**8. Microscope Type and Magnification Combined**

Natural Language:
Which infinity-corrected microscope lenses support magnification of 20× or higher?

Reasoning:
- Filter `microscope_type` for infinity-corrected systems and `magnification_max` for high magnification.

```sql
SELECT model_name, microscope_type, magnification_min, magnification_max,
       numerical_aperture, wd_mm
FROM microscope_lenses
WHERE microscope_type ILIKE '%infinity%'
  AND magnification_max >= 20;
```

---

**9. Tube Length Filter**

Natural Language:
Find all microscope lenses with a 160 mm tube length (DIN standard finite conjugate).

Reasoning:
- Filter `tube_length_mm` for DIN-standard finite conjugate objectives.

```sql
SELECT model_name, tube_length_mm, objective_mount_raw, tube_lens_mount_raw, magnification_max
FROM microscope_lenses
WHERE tube_length_mm = 160;
```

---

## Notes

- **Primary Key:** `model_name`
- `numerical_aperture` is the single most important parameter for microscope objective performance: it determines resolution (`object_resolution_um`), depth of field (`dof_um`), and light collection. Higher NA = better resolution but shallower DOF and shorter working distance.
- `object_resolution_um` is physically related to NA and wavelength by the Rayleigh criterion (Resolution ≈ 0.61 × λ / NA); use both `numerical_aperture` and `object_resolution_um` in queries for completeness.
- `dof_um` is typically very small at high magnifications (sub-micron to a few microns); filter with `>` when looking for forgiving DOF on rough surfaces.
- `microscope_type` distinguishes infinity-corrected (requires separate tube lens) from finite conjugate (self-contained) systems; this determines whether `tube_lens_mount_raw` and `tube_length_mm` are relevant.
- `objective_mount_raw` is the specimen-side thread (e.g., RMS = Royal Microscopical Society thread, M25, M32); `tube_lens_mount_raw` is the intermediate optical coupling mount; `mount_raw` is the camera-side mount — these three are distinct and should not be conflated.
- Four FOV angle column sets (`angle_primary_*` through `angle_quaternary_*`) accommodate the widest range of sensor size configurations across this lens family.
- All `*_raw`, `mount_raw`, `illumination_type`, and `microscope_type` text fields should be queried with `ILIKE` and `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "microscope lens", "objective lens", "tube lens", "numerical aperture", "infinity corrected objective", "high magnification lens", "digital microscopy", "video microscope", "darkfield objective", or "depth of field microscope".

---
