CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_multibuffer` AS
WITH ref AS (
    -- BigQuery działa wyłącznie w GEOGRAPHY (EPSG:4326)
    SELECT ST_GEOGPOINT(19.46701915338524, 51.74357018348951) AS geom
),

-- Lista kategorii
cats AS (
    SELECT DISTINCT category
    FROM `mgr-2025.mgr_2025.dat_poi`
    WHERE category IS NOT NULL
),

-- Liczenie punktów w promieniach dla każdej kategorii
counts AS (
    SELECT
        c.category,

        -- małe promienie
        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 50)
        ) AS cnt_50m,

        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 100)
        ) AS cnt_100m,

        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 500)
        ) AS cnt_500m,

        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 1000)
        ) AS cnt_1000m,

        -- średnie promienie
        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category 
           AND ST_DWithin(p.geom_point_4326, r.geom, 5000)
        ) AS cnt_5000m,

        -- duże promienie
        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 50000)
        ) AS cnt_50000m,

        (SELECT COUNT(*)
         FROM `mgr-2025.mgr_2025.dat_poi` p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_4326, r.geom, 100000)
        ) AS cnt_100000m

    FROM cats c
)

SELECT *
FROM counts;
