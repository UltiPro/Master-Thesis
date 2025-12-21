-- =====================================================================
--   Przeciąć powiększone o 5 km obszary gmin z granicami województw
--   i zmierzyć obciążenie operacji ST_Intersection na dużych danych.
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.geo_polska_buffer_intersection;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.geo_polska_buffer_intersection AS
WITH woj AS (
    SELECT 
        id    AS woj_id,
        nazwa AS woj_name,
        geom_4326_geog
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),
buf AS (
    SELECT
        id AS gmina_id,
        ST_Buffer(geom_4326_geog, 5000) AS geom_buffer_5km_geog
    FROM mgr_2025.geo_polska
    WHERE typ = 'gmina'
)
SELECT
    b.gmina_id,
    w.woj_id,

    -- pole powierzchni w metrach
    ST_Area(
        ST_Intersection(b.geom_buffer_5km_geog, w.geom_4326_geog)
    ) AS area_intersection_m2,

    -- geometria wynikowa (do zapisu / wizualizacji)
    ST_Intersection(
        b.geom_buffer_5km_geog,
        w.geom_4326_geog
    )::geometry AS geom_intersection

FROM buf b
JOIN woj w
    ON ST_Intersects(b.geom_buffer_5km_geog, w.geom_4326_geog);
    