CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.vw_hex_poi_counts` AS
WITH hex_sample AS (
    SELECT *
    FROM `mgr-2025.mgr_2025.geo_hex`
    ORDER BY hex_0125
)
SELECT
    h.hex_0125,
    COUNT(p.id) AS poi_count
FROM hex_sample h
LEFT JOIN `mgr-2025.mgr_2025.dat_poi` p
    ON ST_CONTAINS(h.geom_4326, p.geom_point_4326)
GROUP BY h.hex_0125
ORDER BY h.hex_0125;
