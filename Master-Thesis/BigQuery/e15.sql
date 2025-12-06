CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.vw_hex_road_lengths` AS
WITH hex_sample AS (
    SELECT *
    FROM `mgr-2025.mgr_2025.geo_hex`
    ORDER BY hex_0125
    LIMIT 100000
),
roads AS (
    SELECT
        id,
        highway,
        geom_line_4326 AS geom
    FROM `mgr-2025.mgr_2025.osm_roads`
)
SELECT
    h.hex_0125 AS hex_id,
    SUM(
        ST_LENGTH(
            ST_INTERSECTION(r.geom, h.geom_4326)
        )
    ) AS total_road_length_m
FROM hex_sample h
JOIN roads r
    ON ST_INTERSECTS(r.geom, h.geom_4326)
GROUP BY h.hex_0125
ORDER BY h.hex_0125;
