-- ============================================================
-- Policzenie liczby punktów POI w hexagonach.
-- ============================================================

WITH hex_sample AS (
    SELECT *
    FROM mgr_2025.geo_hex
    ORDER BY hex_0125
)
SELECT 
    h.hex_0125,
    COUNT(p.id) AS poi_count
FROM hex_sample h
LEFT JOIN mgr_2025.dat_poi p
    ON ST_Contains(h.geom_2180, p.geom_point_2180)
GROUP BY h.hex_0125
ORDER BY h.hex_0125;
