CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_border` AS
WITH

-- Jednostki administracyjne: BigQuery GEOGRAPHY (4326)
gmina AS (
    SELECT 
        id,
        geom_4326 AS geom,
        ST_EXTERIORRING(geom_4326) AS boundary
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'gmina'
),

powiat AS (
    SELECT 
        id,
        geom_4326 AS geom,
        ST_EXTERIORRING(geom_4326) AS boundary
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'powiat'
),

woj AS (
    SELECT 
        id,
        geom_4326 AS geom,
        ST_EXTERIORRING(geom_4326) AS boundary
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'województwo'
),

kraj AS (
    SELECT 
        id,
        geom_4326 AS geom,
        ST_EXTERIORRING(geom_4326) AS boundary
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'kraj'
),

-- Limitowana próbka
poi_subset AS (
    SELECT *
    FROM `mgr-2025.mgr_2025.dat_poi`
    ORDER BY id
    LIMIT 1000
)

SELECT
    p.id AS poi_id,

    ST_DISTANCE(p.geom_point_4326, g.boundary)  AS dist_gmina,
    ST_DISTANCE(p.geom_point_4326, pw.boundary) AS dist_powiat,
    ST_DISTANCE(p.geom_point_4326, w.boundary)  AS dist_woj,
    ST_DISTANCE(p.geom_point_4326, k.boundary)  AS dist_kraj

FROM poi_subset p
LEFT JOIN gmina g   ON ST_CONTAINS(g.geom, p.geom_point_4326)
LEFT JOIN powiat pw ON ST_CONTAINS(pw.geom, p.geom_point_4326)
LEFT JOIN woj w     ON ST_CONTAINS(w.geom, p.geom_point_4326)
CROSS JOIN kraj k;
