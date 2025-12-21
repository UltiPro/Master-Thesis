-- ===========================================================================
-- Dla wskazanej ilości punktów POI obliczamy odległość do granicy:
-- - gminy - powiatu - województwa - kraju
-- ===========================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_border;

EXPLAIN (ANALYZE, BUFFERS)
WITH

-- Jednostki administracyjne z boundary
gmina AS (
    SELECT id, geom_2180 AS geom, ST_Boundary(geom_2180) AS boundary
    FROM mgr_2025.geo_polska
    WHERE typ = 'gmina'
),

powiat AS (
    SELECT id, geom_2180 AS geom, ST_Boundary(geom_2180) AS boundary
    FROM mgr_2025.geo_polska
    WHERE typ = 'powiat'
),

woj AS (
    SELECT id, geom_2180 AS geom, ST_Boundary(geom_2180) AS boundary
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),

kraj AS (
    SELECT id, geom_2180 AS geom, ST_Boundary(geom_2180) AS boundary
    FROM mgr_2025.geo_polska
    WHERE typ = 'kraj'
),

-- Limitowana próbka
poi_subset AS (
    SELECT *
    FROM mgr_2025.dat_poi
    LIMIT 1000
)

SELECT
    p.id AS poi_id,

    ST_Distance(p.geom_point_2180, g.boundary)  AS dist_gmina,
    ST_Distance(p.geom_point_2180, pw.boundary) AS dist_powiat,
    ST_Distance(p.geom_point_2180, w.boundary)  AS dist_woj,
    ST_Distance(p.geom_point_2180, k.boundary)  AS dist_kraj

INTO mgr_2025.feat_poi_border
FROM poi_subset p
LEFT JOIN gmina g    ON ST_Contains(g.geom, p.geom_point_2180)
LEFT JOIN powiat pw  ON ST_Contains(pw.geom, p.geom_point_2180)
LEFT JOIN woj w      ON ST_Contains(w.geom, p.geom_point_2180)
CROSS JOIN kraj k;
