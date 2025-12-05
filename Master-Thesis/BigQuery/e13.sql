CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_hex_union_woj` AS
WITH woj AS (
    SELECT 
        id AS woj_id,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'województwo'
),
hex_sample AS (
    SELECT
        hex_0125,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_hex`
    ORDER BY hex_0125
    LIMIT 1000000
)
SELECT
    w.woj_id,
    ST_UNION_AGG(h.geom) AS geom_union
FROM woj w
JOIN hex_sample h
    ON ST_INTERSECTS(h.geom, w.geom)
GROUP BY w.woj_id;
