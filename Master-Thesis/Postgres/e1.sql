-- =====================================================================
-- Wyszukiwanie najbliższego punktu POI do zadanego punktu
-- =====================================================================

EXPLAIN (ANALYZE, BUFFERS)
WITH ref AS (
    SELECT ST_Transform(
        ST_SetSRID(ST_MakePoint(19.46701915338524, 51.74357018348951), 4326),
        2180
    ) AS geom
)
SELECT *
FROM mgr_2025.dat_poi, ref
ORDER BY geom_point_2180 <-> ref.geom
LIMIT 1;
