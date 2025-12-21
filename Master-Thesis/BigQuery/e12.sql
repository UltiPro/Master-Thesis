CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_roads_near_poi` AS
WITH poi_sample AS (
    SELECT *
    FROM `mgr-2025.mgr_2025.dat_poi`
    LIMIT 1000
)
SELECT
    p.id AS poi_id,
    SUM(ST_LENGTH(r.geom_line_4326)) AS roads_length_m_500m
FROM poi_sample p
JOIN `mgr-2025.mgr_2025.osm_roads` r
    ON ST_DWITHIN(p.geom_point_4326, r.geom_line_4326, 500)
GROUP BY p.id;
