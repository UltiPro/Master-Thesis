-- =====================================================================
-- Najdłuższy odcinek drogi per highway
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_road_longest_per_category;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.feat_road_longest_per_category AS
WITH road_lengths AS (
    SELECT
        id,
        highway,
        ST_Length(geom_line_2180) AS length_m
    FROM mgr_2025.osm_roads
)
SELECT DISTINCT ON (highway)
    highway,
    id AS road_id,
    length_m
FROM road_lengths
ORDER BY highway, length_m DESC;
