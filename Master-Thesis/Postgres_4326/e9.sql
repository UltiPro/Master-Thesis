-- =====================================================================
-- Średnia długość odcinków dróg per highway (EPSG:4326)
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_road_avg_length;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.feat_road_avg_length AS
SELECT
    highway,
    AVG(ST_Length(geom_line_4326_geog)) AS avg_length_m
FROM mgr_2025.osm_roads
GROUP BY highway;
