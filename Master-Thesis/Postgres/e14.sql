-- ============================================================
-- Policzenie liczby punktów POI w hexagonach.
-- ============================================================

DROP TABLE IF EXISTS mgr_2025.vw_hex_poi_counts;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.vw_hex_poi_counts AS
SELECT 
    h.hex_0125,
    COUNT(p.id) AS poi_count
FROM mgr_2025.geo_hex h
LEFT JOIN mgr_2025.dat_poi p
    ON ST_Contains(h.geom_2180, p.geom_point_2180)
GROUP BY h.hex_0125;
