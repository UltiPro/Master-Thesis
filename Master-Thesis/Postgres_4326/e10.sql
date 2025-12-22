-- =====================================================================
-- Najbliższa droga dla każdego POI
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_nearest_road;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.feat_poi_nearest_road AS
SELECT
    p.id AS poi_id,
    r.id AS road_id,
    ST_Distance(p.geom_point_4326_geog, r.geom_line_4326_geog) AS distance_m
FROM mgr_2025.dat_poi p
JOIN LATERAL (
    SELECT id, geom_line_4326_geog
    FROM mgr_2025.osm_roads
    ORDER BY geom_line_4326_geog <-> p.geom_point_4326_geog
    LIMIT 1
) r ON TRUE;
