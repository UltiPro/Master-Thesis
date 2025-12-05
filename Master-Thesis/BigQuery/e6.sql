CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_polska_buffer_intersection` AS
WITH woj AS (
    SELECT
        id AS woj_id,
        nazwa AS woj_name,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'województwo'
),

buf AS (
    SELECT
        id AS gmina_id,
        ST_BUFFER(geom_4326, 5000) AS geom_buffer_5km
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'gmina'
)

SELECT
    b.gmina_id,
    w.woj_id,

    -- powierzchnia części wspólnej w m²
    ST_AREA(ST_INTERSECTION(b.geom_buffer_5km, w.geom)) AS area_intersection_m2,

    -- geometria przecięcia
    ST_INTERSECTION(b.geom_buffer_5km, w.geom) AS geom_intersection

FROM buf b
JOIN woj w
    ON ST_INTERSECTS(b.geom_buffer_5km, w.geom)
WHERE ST_INTERSECTION(b.geom_buffer_5km, w.geom) IS NOT NULL;
