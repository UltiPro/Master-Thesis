-- ===========================================================================
-- Voronoi + przecięcia z województwami (EPSG:4326)
-- ===========================================================================

DROP TABLE IF EXISTS mgr_2025.voronoi_limited;

EXPLAIN (ANALYZE, BUFFERS)
CREATE TABLE mgr_2025.voronoi_limited AS
WITH 

-- LIMIT N punktów POI (EPSG:4326, 2D)
pts AS (
    SELECT geom_point_4326
    FROM mgr_2025.dat_poi
    LIMIT 1000
),

-- Ramka otaczająca (w stopniach)
bbox AS (
    SELECT ST_Envelope(ST_Collect(geom_point_4326)) AS env
    FROM pts
),

-- Diagram Voronoi (czysto geometryczny, planar)
voronoi AS (
    SELECT 
        (ST_Dump(
            ST_VoronoiPolygons(
                (SELECT ST_Collect(geom_point_4326) FROM pts),
                0,
                (SELECT env FROM bbox)
            )
        )).geom AS cell
),

-- Województwa (EPSG:4326)
woj AS (
    SELECT
        id,
        nazwa AS name,
        geom_4326
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),

-- Przecięcia (liczone dokładnie raz)
intersections AS (
    SELECT
        w.id   AS woj_id,
        w.name AS woj_name,
        v.cell,
        ST_Intersection(v.cell, w.geom_4326) AS geom_intersection
    FROM voronoi v
    JOIN woj w
        ON ST_Intersects(v.cell, w.geom_4326)
)

-- Agregacja + miary metryczne
SELECT
    woj_id,
    woj_name,
    COUNT(*) AS voronoi_cell_count,
    SUM(
        ST_Area(geom_intersection::geography)
    ) AS area_sum_m2
FROM intersections
WHERE geom_intersection IS NOT NULL
GROUP BY woj_id, woj_name;
