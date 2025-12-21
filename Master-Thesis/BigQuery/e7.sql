CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_per_admin` AS
SELECT
    a.id,
    a.nazwa,
    a.typ,
    COUNT(p.id) AS poi_count
FROM `mgr-2025.mgr_2025.geo_polska` a
LEFT JOIN `mgr-2025.mgr_2025.dat_poi` p
    ON ST_CONTAINS(a.geom_4326, p.geom_point_4326)
GROUP BY 
    a.id,
    a.nazwa,
    a.typ;
