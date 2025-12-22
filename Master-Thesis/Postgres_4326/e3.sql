-- ===========================================================================
-- Dla jednego punktu referencyjnego obliczamy, ile punktów 
-- z każdej kategorii znajduje się w kolejnych promieniach:
-- 50m, 100m, 500m, 1000m, 5000m, 50000m, 100000m.
-- ===========================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_multibuffer;

EXPLAIN (ANALYZE, BUFFERS)
WITH ref AS (
    SELECT
        ST_GeogFromText(
            'POINT(19.46701915338524 51.74357018348951)'
        ) AS geog
),

cats AS (
    SELECT DISTINCT category
    FROM mgr_2025.dat_poi
    WHERE category IS NOT NULL
),

counts AS (
    SELECT
        c.category,
        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 50))       AS cnt_50m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 100))      AS cnt_100m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 500))      AS cnt_500m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 1000))     AS cnt_1000m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 5000))     AS cnt_5000m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 50000))    AS cnt_50000m,

        (SELECT COUNT(*) FROM mgr_2025.dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326_geog, r.geog, 100000))   AS cnt_100000m
    FROM cats c
)

SELECT *
INTO mgr_2025.feat_poi_multibuffer
FROM counts;
