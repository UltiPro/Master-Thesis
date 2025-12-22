-- =====================================================================
-- Łączna długość dróg w hexagonach
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.vw_hex_road_lengths;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.vw_hex_road_lengths AS
SELECT
    h.hex_0125 AS hex_id,
    SUM(
        ST_Length(
            ST_Intersection(
                r.geom_line_4326,
                h.geom_4326
            )::geography
        )
    ) AS total_road_length_m
FROM mgr_2025.geo_hex h
JOIN mgr_2025.osm_roads r
    ON ST_Intersects(r.geom_line_4326, h.geom_4326)
GROUP BY h.hex_0125;
