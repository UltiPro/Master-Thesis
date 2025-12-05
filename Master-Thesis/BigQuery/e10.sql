CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_nearest_road` AS
SELECT
    p.id AS poi_id,
    r.id AS road_id,
    ST_DISTANCE(p.geom_point_4326, r.geom_line_4326) AS distance_m
FROM `mgr-2025.mgr_2025.dat_poi` p
CROSS JOIN LATERAL (
    SELECT id, geom_line_4326
    FROM `mgr-2025.mgr_2025.osm_roads`
    ORDER BY ST_DISTANCE(geom_line_4326, p.geom_point_4326)
    LIMIT 1
) r
ORDER BY p.id;
