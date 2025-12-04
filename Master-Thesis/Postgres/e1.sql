-- =====================================================================
-- Wyszukiwanie najbliższego punktu POI do zadanego punktu
-- =====================================================================

SELECT *
FROM mgr_2025.dat_poi
ORDER BY geom_point_4326 <-> ST_SetSRID(ST_MakePoint(19.46701915338524, 51.74357018348951), 4326)
LIMIT 1;
