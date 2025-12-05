CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_hex_woj_join` AS
WITH woj AS (
    SELECT 
        id AS woj_id,
        nazwa AS woj_name,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'województwo'
),
hex_sample AS (
    SELECT 
        hex_0125 AS hex_id,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_hex`
    ORDER BY hex_0125
    LIMIT 1000
)
SELECT
    h.hex_id,
    w.woj_id,
    ST_AREA(h.geom) AS area_hex_m2,
    ST_AREA(ST_INTERSECTION(h.geom, w.geom)) AS area_intersection_m2
FROM hex_sample h
JOIN woj w
    ON ST_INTERSECTS(h.geom, w.geom)
WHERE ST_INTERSECTION(h.geom, w.geom) IS NOT NULL;
