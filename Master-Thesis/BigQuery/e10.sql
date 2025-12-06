-- należało nałożyć bufor 500 m wokół POI i znaleźć najbliższą drogę z OSM
-- inaczej BQ nie radzi sobie z dużą liczbą geometrii i zwraca błąd przekroczenia pamięci

CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_nearest_road` AS
WITH candidate_roads AS (
    SELECT
        p.id AS poi_id,
        r.id AS road_id,
        r.geom_line_4326 AS geom,
        ST_DISTANCE(p.geom_point_4326, r.geom_line_4326) AS dist
    FROM `mgr-2025.mgr_2025.dat_poi` p
    JOIN `mgr-2025.mgr_2025.osm_roads` r
    ON ST_DWITHIN(p.geom_point_4326, r.geom_line_4326, 500)  -- bufor 500 m
)
SELECT
    poi_id,
    road_id,
    dist AS distance_m
FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY poi_id ORDER BY dist ASC) AS rn
    FROM candidate_roads
)
WHERE rn = 1
ORDER BY poi_id;
