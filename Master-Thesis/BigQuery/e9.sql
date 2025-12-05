CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_road_avg_length` AS
SELECT
    highway,
    AVG(ST_LENGTH(geom_line_4326)) AS avg_length_m
FROM `mgr-2025.mgr_2025.osm_roads`
GROUP BY highway
ORDER BY avg_length_m DESC;
