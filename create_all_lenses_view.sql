CREATE OR REPLACE VIEW ragav.all_lenses AS

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    TRUE AS is_coaxial,
    'Other' AS resolution_target
FROM ragav.coaxial_illumination_line_scan_lens

UNION ALL

SELECT 
    model_name,
    list_price,
    CAST(NULL AS numeric) AS magnification_min,
    CAST(NULL AS numeric) AS magnification_max,
    FALSE AS is_coaxial,
    'Other' AS resolution_target
FROM ragav.standard_telecentric_lenses_2_3_inch

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '4K' AS resolution_target
FROM ragav.line_scan_lens_4k7u

UNION ALL

SELECT 
    model_name,
    list_price,
    CAST(NULL AS numeric) AS magnification_min,
    CAST(NULL AS numeric) AS magnification_max,
    FALSE AS is_coaxial,
    'Other' AS resolution_target
FROM ragav.standard_telecentric_lenses_1_1_inch

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '4K' AS resolution_target
FROM ragav.new_series_line_scan_lens_4k7u

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '8K' AS resolution_target
FROM ragav.line_scan_lens_8k5u

UNION ALL

SELECT 
    model_name,
    list_price,
    CAST(NULL AS numeric) AS magnification_min,
    CAST(NULL AS numeric) AS magnification_max,
    FALSE AS is_coaxial,
    'Other' AS resolution_target
FROM ragav.telecentric_lenses_65mp

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '8K' AS resolution_target
FROM ragav.line_scan_lens_8k7u

UNION ALL

SELECT 
    model_name,
    list_price,
    CAST(NULL AS numeric) AS magnification_min,
    CAST(NULL AS numeric) AS magnification_max,
    FALSE AS is_coaxial,
    'Other' AS resolution_target
FROM ragav.non_standard_telecentric_lenses

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '16K' AS resolution_target
FROM ragav.line_scan_lens_16k3_5u

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '16K' AS resolution_target
FROM ragav.line_scan_lens_16k5u

UNION ALL

SELECT 
    model_name,
    list_price,
    magnification_min,
    magnification_max,
    FALSE AS is_coaxial,
    '12K' AS resolution_target
FROM ragav.line_scan_lens_12k5u;
