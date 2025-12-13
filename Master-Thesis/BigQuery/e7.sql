CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_per_admin` AS
WITH admin_units AS (
    SELECT 
        id AS admin_id,
        nazwa AS admin_name,
        typ  AS admin_type,
        geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ IN ('kraj', 'województwo', 'powiat', 'gmina')
)
SELECT
    a.admin_id,
    a.admin_name,
    a.admin_type,
    COUNT(p.id) AS poi_count
FROM admin_units a
LEFT JOIN `mgr-2025.mgr_2025.dat_poi` p
    ON ST_CONTAINS(a.geom, p.geom_point_4326)
GROUP BY 
    a.admin_id, 
    a.admin_name, 
    a.admin_type;
