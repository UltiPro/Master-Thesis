-- =====================================================================
-- Długość dróg w promieniu 500 m od punktów POI (EPSG:4326)
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_roads_near_poi;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.feat_roads_near_poi AS
WITH poi_sample AS (
    SELECT
        id,
        geom_point_4326
    FROM mgr_2025.dat_poi
    LIMIT 1000
)
SELECT
    p.id AS poi_id,
    SUM(
        ST_Length(r.geom_line_4326::geography)
    ) AS roads_length_m_500m
FROM poi_sample p
JOIN mgr_2025.osm_roads r
    ON ST_DWithin(
        p.geom_point_4326::geography,
        r.geom_line_4326::geography,
        500
    )
GROUP BY p.id;
