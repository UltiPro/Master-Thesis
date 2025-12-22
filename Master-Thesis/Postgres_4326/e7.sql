-- =====================================================================
--   Obliczyć liczbę punktów POI znajdujących się w granicach
--   każdej jednostki administracyjnej na 4 poziomach:
--       kraj → województwo → powiat → gmina
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_poi_per_admin;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.feat_poi_per_admin AS
SELECT
    a.id,
    a.nazwa,
    a.typ,
    COUNT(p.id) AS poi_count
FROM mgr_2025.geo_polska a
LEFT JOIN mgr_2025.dat_poi p
    ON ST_Contains(a.geom_4326, p.geom_point_4326)
GROUP BY
    a.id,
    a.nazwa,
    a.typ;
