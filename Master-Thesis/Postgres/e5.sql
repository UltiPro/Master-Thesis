-- =====================================================================
--   Obliczyć trzy podstawowe cechy geometryczne dla wszystkich 
--   jednostek administracyjnych w Polsce:
--       • powierzchnię (ST_Area)
--       • długość granicy (ST_Perimeter)
--       • centroid (ST_Centroid)
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.geo_polska_geom_features;

CREATE TABLE mgr_2025.geo_polska_geom_features AS
SELECT
    id,
    nazwa,
    typ,
    ST_Area(geom_2180)      AS area_m2,
    ST_Perimeter(geom_2180) AS perimeter_m,
    ST_Centroid(geom_2180)  AS centroid_2180
FROM mgr_2025.geo_polska
ORDER BY id;
