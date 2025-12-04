-- =====================================================================
-- Średnia długość odcinków dróg per highway
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.feat_road_avg_length;

CREATE TABLE mgr_2025.feat_road_avg_length AS
SELECT
    highway,
    AVG(ST_Length(geom_line_2180)) AS avg_length_m
FROM mgr_2025.osm_roads
GROUP BY highway
ORDER BY avg_length_m DESC;
