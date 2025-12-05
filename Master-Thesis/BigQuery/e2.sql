CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_nearest` AS
WITH ref AS (
    -- Punkt odniesienia w BigQuery musi być w GEOGRAPHY 4326
    SELECT ST_GEOGPOINT(19.46701915338524, 51.74357018348951) AS geom
),

-- Pobranie listy kategorii
cats AS (
    SELECT DISTINCT category
    FROM `mgr-2025.mgr_2025.dat_poi`
    WHERE category IS NOT NULL
),

-- Najbliższy POI dla każdej kategorii
nearest AS (
    SELECT 
        c.category,
        nn.id AS nearest_poi_id,
        nn.dist AS distance_m
    FROM cats c
    CROSS JOIN ref r
    CROSS JOIN LATERAL (
        SELECT 
            id,
            ST_DISTANCE(geom_point_4326, r.geom) AS dist
        FROM `mgr-2025.mgr_2025.dat_poi`
        WHERE category = c.category
        ORDER BY ST_DISTANCE(geom_point_4326, r.geom)
        LIMIT 1
    ) AS nn
)

SELECT * FROM nearest;
