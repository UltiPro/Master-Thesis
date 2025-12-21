CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.vw_hex_road_lengths` AS
SELECT
    h.hex_0125 AS hex_id,
    SUM(
        ST_LENGTH(
            ST_INTERSECTION(r.geom_line_4326, h.geom_4326)
        )
    ) AS total_road_length_m
FROM `mgr-2025.mgr_2025.geo_hex` h
JOIN `mgr-2025.mgr_2025.osm_roads` r
    ON ST_INTERSECTS(r.geom_line_4326, h.geom_4326)
GROUP BY h.hex_0125;
