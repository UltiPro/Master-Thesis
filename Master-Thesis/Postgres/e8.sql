-- =====================================================================
-- Zmierzyć wydajność generowania diagramu Voronoi dla wybranej liczby
-- punktów POI (N), a następnie ocenić koszt przecięć komórek Voronoi
-- z granicami województw.
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.voronoi_limited;

CREATE TABLE mgr_2025.voronoi_limited AS
WITH 

-- Pobranie LIMIT N punktów POI
pts AS (
    SELECT geom_point_2180
    FROM mgr_2025.dat_poi
    ORDER BY id
    LIMIT 1000
),

-- Wyliczenie ramki otaczającej (envelope)
bbox AS (
    SELECT ST_Envelope(ST_Collect(geom_point_2180)) AS env
    FROM pts
),

-- Diagram Voronoi (dump → rozbicie multipolygonów)
voronoi AS (
    SELECT 
        (ST_Dump(
            ST_VoronoiPolygons(
                (SELECT ST_Collect(geom_point_2180) FROM pts),
                0,                           -- tolerancja
                (SELECT env FROM bbox)::geometry
            )
        )).geom AS cell
),

-- Województwa
woj AS (
    SELECT id, nazwa AS name, geom_2180
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
)

-- Przecięcie Voronoi–województwa + agregacja
SELECT
    w.id   AS woj_id,
    w.name AS woj_name,
    COUNT(*) AS voronoi_cell_count,
    SUM(ST_Area(ST_Intersection(v.cell, w.geom_2180))) AS area_sum_m2
FROM voronoi v
JOIN woj w
    ON ST_Intersects(v.cell, w.geom_2180)
GROUP BY w.id, w.name
ORDER BY w.id;
