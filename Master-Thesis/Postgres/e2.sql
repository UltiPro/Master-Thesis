-- ==========================================================================================
-- Wyszukiwanie najbliższego punktu POI według każdej kategorii do zadanego punktu.
-- ==========================================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_nearest;

WITH ref AS (
    SELECT ST_Transform(
        ST_SetSRID(ST_MakePoint(19.46701915338524, 51.74357018348951), 4326),
        2180
    ) AS geom
),

-- Pobranie listy kategorii
cats AS (
    SELECT DISTINCT category
    FROM mgr_2025.dat_poi
    WHERE category IS NOT NULL
),

-- Najbliższy POI dla każdej kategorii (K zapytań KNN)
nearest AS (
    SELECT 
        c.category,
        nn.id                     AS nearest_poi_id,
        nn.dist                   AS distance_m
    FROM cats c
    CROSS JOIN ref r
    CROSS JOIN LATERAL (
        SELECT 
            id,
            (geom_point_2180 <-> r.geom) AS dist
        FROM mgr_2025.dat_poi
        WHERE category = c.category
        ORDER BY geom <-> r.geom
        LIMIT 1
    ) nn
)

SELECT *
INTO mgr_2025.feat_poi_nearest
FROM nearest;
