CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_nearest` AS
WITH ref AS (
    SELECT ST_GEOGPOINT(19.46701915338524, 51.74357018348951) AS geom
),

poi_with_dist AS (
    SELECT
        category,
        id AS poi_id,
        ST_DISTANCE(geom_point_4326, (SELECT geom FROM ref)) AS dist
    FROM `mgr-2025.mgr_2025.dat_poi`
    WHERE category IS NOT NULL
),

ranked AS (
    SELECT
        category,
        poi_id AS nearest_poi_id,
        dist AS distance_m,
        ROW_NUMBER() OVER (
            PARTITION BY category
            ORDER BY dist ASC
        ) AS rn
    FROM poi_with_dist
)

SELECT
    category,
    nearest_poi_id,
    distance_m
FROM ranked
WHERE rn = 1
ORDER BY category;
