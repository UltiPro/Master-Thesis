CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_road_longest_per_category` AS
WITH road_lengths AS (
    SELECT
        id,
        highway,
        ST_LENGTH(geom_line_4326) AS length_m
    FROM `mgr-2025.mgr_2025.osm_roads`
)
SELECT
    highway,
    id AS road_id,
    length_m
FROM road_lengths
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY highway
    ORDER BY length_m DESC
) = 1;
