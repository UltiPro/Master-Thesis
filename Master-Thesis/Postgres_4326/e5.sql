-- =====================================================================
--   Obliczyć trzy podstawowe cechy geometryczne dla wszystkich 
--   jednostek administracyjnych w Polsce:
--       • powierzchnię (ST_Area)
--       • długość granicy (ST_Perimeter)
--       • centroid (ST_Centroid)
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.geo_polska_geom_features;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.geo_polska_geom_features AS
SELECT
    id,
    nazwa,
    typ,
    ST_Area(geom_4326_geog)        AS area_m2,
    ST_Perimeter(geom_4326_geog)   AS perimeter_m,
    ST_Centroid(geom_4326_geog)    AS centroid_4326
FROM mgr_2025.geo_polska;
