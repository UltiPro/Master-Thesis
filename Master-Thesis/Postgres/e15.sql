-- =====================================================================
-- Łączna długość dróg w hexagonach
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.vw_hex_road_lengths;

CREATE TABLE mgr_2025.vw_hex_road_lengths AS
WITH hex_sample AS (
    SELECT *
    FROM mgr_2025.geo_hex
    ORDER BY hex_0125
),
roads AS (
    SELECT
        id,
        highway,
        geom_line_2180
    FROM mgr_2025.osm_roads
)
SELECT
    h.hex_0125 AS hex_id,
    SUM(ST_Length(ST_Intersection(r.geom_line_2180, h.geom_2180))) AS total_road_length_m
FROM hex_sample h
JOIN roads r
    ON ST_Intersects(r.geom_line_2180, h.geom_2180)
GROUP BY h.hex_0125
ORDER BY h.hex_0125;
