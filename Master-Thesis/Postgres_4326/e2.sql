-- ==========================================================================================
-- Wyszukiwanie najbliższego punktu POI według każdej kategorii do zadanego punktu (geography)
-- ==========================================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_nearest;

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

nearest AS (
    SELECT 
        c.category,
        nn.id   AS nearest_poi_id,
        nn.dist AS distance_m
    FROM cats c
    CROSS JOIN ref r
    CROSS JOIN LATERAL (
        SELECT 
            id,
            (geom_point_4326_geog <-> r.geog) AS dist
        FROM mgr_2025.dat_poi
        WHERE category = c.category
        ORDER BY geom_point_4326_geog <-> r.geog
        LIMIT 1
    ) nn
)

SELECT *
INTO mgr_2025.feat_poi_nearest
FROM nearest;
