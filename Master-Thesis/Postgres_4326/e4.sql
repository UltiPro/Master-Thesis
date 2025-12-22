-- ===========================================================================
-- Dla wskazanej ilości punktów POI obliczamy odległość do granicy:
-- - gminy - powiatu - województwa - kraju
-- ===========================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_border;

EXPLAIN (ANALYZE, BUFFERS)
WITH

gmina AS (
    SELECT
        id,
        geom_4326,
        ST_Boundary(geom_4326) AS boundary_geom
    FROM mgr_2025.geo_polska
    WHERE typ = 'gmina'
),

powiat AS (
    SELECT
        id,
        geom_4326,
        ST_Boundary(geom_4326) AS boundary_geom
    FROM mgr_2025.geo_polska
    WHERE typ = 'powiat'
),

woj AS (
    SELECT
        id,
        geom_4326,
        ST_Boundary(geom_4326) AS boundary_geom
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),

kraj AS (
    SELECT
        id,
        geom_4326,
        ST_Boundary(geom_4326) AS boundary_geom
    FROM mgr_2025.geo_polska
    WHERE typ = 'kraj'
),

poi_subset AS (
    SELECT
        id,
        geom_point_4326,
        geom_point_4326_geog
    FROM mgr_2025.dat_poi
    LIMIT 1000
)

SELECT
    p.id AS poi_id,

    ST_Distance(p.geom_point_4326_geog, g.boundary_geom::geography)  AS dist_gmina,
    ST_Distance(p.geom_point_4326_geog, pw.boundary_geom::geography) AS dist_powiat,
    ST_Distance(p.geom_point_4326_geog, w.boundary_geom::geography)  AS dist_woj,
    ST_Distance(p.geom_point_4326_geog, k.boundary_geom::geography)  AS dist_kraj

INTO mgr_2025.feat_poi_border
FROM poi_subset p
LEFT JOIN gmina g   ON ST_Contains(g.geom_4326, p.geom_point_4326)
LEFT JOIN powiat pw ON ST_Contains(pw.geom_4326, p.geom_point_4326)
LEFT JOIN woj w     ON ST_Contains(w.geom_4326, p.geom_point_4326)
CROSS JOIN kraj k;
