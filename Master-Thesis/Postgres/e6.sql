-- =====================================================================
--   Przeciąć powiększone o 5 km obszary gmin z granicami województw
--   i zmierzyć obciążenie operacji ST_Intersection na dużych danych.
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.geo_polska_buffer_intersection;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.geo_polska_buffer_intersection AS
WITH woj AS (
    SELECT 
        id   AS woj_id,
        nazwa AS woj_name,
        geom_2180
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),
buf AS (
    SELECT
        id   AS gmina_id,
        ST_Buffer(geom_2180, 5000) AS geom_buffer_5km
    FROM mgr_2025.geo_polska
    WHERE typ = 'gmina'
)
SELECT
    b.gmina_id,
    w.woj_id,
    ST_Area(ST_Intersection(b.geom_buffer_5km, w.geom_2180)) AS area_intersection_m2,
    ST_Intersection(b.geom_buffer_5km, w.geom_2180)          AS geom_intersection
FROM buf b
JOIN woj w
    ON ST_Intersects(b.geom_buffer_5km, w.geom_2180)
WHERE ST_Intersection(b.geom_buffer_5km, w.geom_2180) IS NOT NULL;
