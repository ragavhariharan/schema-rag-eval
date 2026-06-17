# Table: magnifying_lenses

## Purpose

Stores specifications for **magnifying lenses** — optical components designed to produce magnified images of small objects or features for direct visual inspection or camera-based imaging. In machine vision contexts, magnifying lenses function as relay or projection lenses that increase the apparent size of a target at the sensor plane, and are commonly used as auxiliary magnification attachments, loupe-style inspection devices, or integrated components in video microscopy systems. They are applied in quality control of microelectronics, PCB inspection, medical device assembly verification, and fine mechanical part inspection.

This table supports engineering lookups by magnification range, sensor size compatibility, mount type, and supported illumination wavelength range. It enables SQL-based retrieval for compatibility checks and specification filtering in RAG pipelines.

---

## Attributes

| Column | Meaning | Datatype | Notes |
|---|---|---|---|
| model_name | Unique product identifier for the magnifying lens model | text | Primary key. Used as the main lookup key across all queries. |
| list_price | Catalogue sales price of the lens | numeric | Monetary value. Currency assumed to be USD unless otherwise specified. |
| magnification_raw | Raw text representation of the magnification value or range | text | Original source string (e.g., "2×", "0.5× – 4×"). Preserved for display. |
| magnification_min | Minimum optical magnification ratio supported | numeric | Dimensionless. Smaller = lower magnification / wider coverage. |
| magnification_max | Maximum optical magnification ratio supported | numeric | Dimensionless. Larger = higher magnification / finer detail. |
| sensor_size_raw | Raw text describing the compatible image sensor size | text | E.g., "1/2 inch", "2/3 inch". Use `ILIKE` for filtering. |
| mount_raw | Raw text describing the camera or system mount type | text | E.g., "C-mount", "RMS thread". Use `ILIKE` for filtering. |
| wavelength_raw | Raw text describing the supported illumination wavelength range | text | Original source string (e.g., "400–700 nm", "visible"). Preserved for display. |
| wavelength_min_nm | Minimum supported wavelength in nanometers | numeric | Lower bound of the usable spectral range. Units: nm. |
| wavelength_max_nm | Maximum supported wavelength in nanometers | numeric | Upper bound of the usable spectral range. Units: nm. |

---

## Relationships

### Explicit Relationships

No explicit foreign key relationships.

### Inferred Logical Relationships

* `magnifying_lenses` ↔ `microscope_lenses`: both provide magnified imaging. Magnifying lenses cover lower magnification ranges (typically 0.5×–10×); microscope lenses (objective + tube lens systems) cover higher ranges (5×–200×+). Cross-compare by `magnification_max`.
* `magnifying_lenses` ↔ `macro_lenses`: macro lenses provide similar magnification ranges but with explicit working distance and aperture specs. Magnifying lenses may be simpler relay-type optics with fewer mechanical parameters.
* `wavelength_min_nm` / `wavelength_max_nm` link logically to `spectral_lenses.wavelength_min_nm` / `wavelength_max_nm` for cross-family spectral range comparisons.

---

## Example Queries

**1. Specification Lookup**

Natural Language:
List all magnifying lenses with their magnification range and supported wavelength range.

Reasoning:
- Select identifying and key specification columns.
- No filtering — return all rows.

```sql
SELECT model_name, magnification_min, magnification_max, wavelength_min_nm, wavelength_max_nm
FROM magnifying_lenses;
```

---

**2. Magnification Range Filter**

Natural Language:
Find all magnifying lenses that support a magnification of 4× or higher.

Reasoning:
- Filter `magnification_max` for lenses capable of high magnification output.

```sql
SELECT model_name, magnification_min, magnification_max, magnification_raw
FROM magnifying_lenses
WHERE magnification_max >= 4;
```

---

**3. Magnification Overlap Filter**

Natural Language:
Which magnifying lenses support a magnification of 2×?

Reasoning:
- Filter where the target magnification (2×) falls within the supported range.

```sql
SELECT model_name, magnification_min, magnification_max, mount_raw
FROM magnifying_lenses
WHERE magnification_min <= 2
  AND magnification_max >= 2;
```

---

**4. Wavelength Range Filter**

Natural Language:
Find all magnifying lenses that support NIR wavelengths up to 900 nm.

Reasoning:
- Filter `wavelength_max_nm` for lenses with extended NIR coverage.

```sql
SELECT model_name, wavelength_min_nm, wavelength_max_nm, wavelength_raw
FROM magnifying_lenses
WHERE wavelength_max_nm >= 900;
```

---

**5. Visible Spectrum Filter**

Natural Language:
Which magnifying lenses are optimized for the visible spectrum (400–700 nm)?

Reasoning:
- Filter for lenses whose wavelength range covers the standard visible band.

```sql
SELECT model_name, wavelength_min_nm, wavelength_max_nm, magnification_min, magnification_max
FROM magnifying_lenses
WHERE wavelength_min_nm <= 400
  AND wavelength_max_nm >= 700;
```

---

**6. Mount Type Filter**

Natural Language:
List all magnifying lenses with a C-mount.

Reasoning:
- Filter `mount_raw` using `ILIKE` for C-mount compatibility.

```sql
SELECT model_name, mount_raw, magnification_min, magnification_max, sensor_size_raw
FROM magnifying_lenses
WHERE mount_raw ILIKE '%C%';
```

---

**7. Sensor Size and Magnification Combined**

Natural Language:
Which magnifying lenses are compatible with a 2/3-inch sensor and support magnification of at least 2×?

Reasoning:
- Combine `sensor_size_raw` and `magnification_max` filters.

```sql
SELECT model_name, sensor_size_raw, magnification_min, magnification_max, mount_raw
FROM magnifying_lenses
WHERE sensor_size_raw ILIKE '%2/3%'
  AND magnification_max >= 2;
```

---

## Notes

- **Primary Key:** `model_name`
- `magnifying_lenses` has a minimal schema compared to other lens families — no aperture, working distance, or distortion columns — reflecting the simpler specification set of relay-type magnification optics.
- `magnification_min` and `magnification_max` define the supported range; use a range-overlap query pattern (`min <= target AND max >= target`) when filtering for a specific magnification value.
- `wavelength_min_nm` and `wavelength_max_nm` are key for multi-spectral applications; verify that the lens covers the illumination wavelength used in the system (e.g., UV at 365 nm, green laser at 532 nm, NIR at 850 nm).
- `mount_raw` and `sensor_size_raw` are free-text fields; always use `ILIKE` with `%` wildcards.
- This table is optimized for RAG chunk retrieval when queries mention "magnifying lens", "magnification attachment", "relay lens", "video magnifier", "zoom magnifier", "loupe lens", or "magnification optic".

---
