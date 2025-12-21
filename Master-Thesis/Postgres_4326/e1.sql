-- =====================================================================
-- Wyszukiwanie najbliższego punktu POI do zadanego punktu (geography)
-- =====================================================================

EXPLAIN (ANALYZE, BUFFERS)
WITH ref AS (
    SELECT
        ST_GeogFromText(
            'POINT(19.46701915338524 51.74357018348951)'
        ) AS geog
)
SELECT *
FROM mgr_2025.dat_poi, ref
ORDER BY geom_point_4326_geog <-> ref.geog
LIMIT 1;
