CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.feat_poi_border` AS
WITH
-- ============================
-- Dane źródłowe
-- ============================
gmina AS (
    SELECT id AS gmina_id, geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'gmina'
),
powiat AS (
    SELECT id AS powiat_id, geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'powiat'
),
woj AS (
    SELECT id AS woj_id, geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'województwo'
),
kraj AS (
    SELECT id AS kraj_id, geom_4326 AS geom
    FROM `mgr-2025.mgr_2025.geo_polska`
    WHERE typ = 'kraj'
),

-- Pobieramy POI (1000 jak w PostGIS)
poi_subset AS (
    SELECT *
    FROM `mgr-2025.mgr_2025.dat_poi`
    LIMIT 1000
),

-- ============================
-- GMINA — wybór właściwego polygona i dystansu
-- ============================
gmina_match AS (
    SELECT
        p.id,
        g.gmina_id,
        ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(g.geom)) AS dist,
        ROW_NUMBER() OVER (
            PARTITION BY p.id 
            ORDER BY ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(g.geom))
        ) AS rn
    FROM poi_subset p
    JOIN gmina g
      ON ST_CONTAINS(g.geom, p.geom_point_4326)
),
gmina_best AS (
    SELECT id, gmina_id, dist AS dist_gmina
    FROM gmina_match WHERE rn = 1
),

-- ============================
-- POWIAT
-- ============================
powiat_match AS (
    SELECT
        p.id,
        pw.powiat_id,
        ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(pw.geom)) AS dist,
        ROW_NUMBER() OVER (
            PARTITION BY p.id 
            ORDER BY ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(pw.geom))
        ) AS rn
    FROM poi_subset p
    JOIN powiat pw
      ON ST_CONTAINS(pw.geom, p.geom_point_4326)
),
powiat_best AS (
    SELECT id, powiat_id, dist AS dist_powiat
    FROM powiat_match WHERE rn = 1
),

-- ============================
-- WOJEWÓDZTWO
-- ============================
woj_match AS (
    SELECT
        p.id,
        w.woj_id,
        ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(w.geom)) AS dist,
        ROW_NUMBER() OVER (
            PARTITION BY p.id 
            ORDER BY ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(w.geom))
        ) AS rn
    FROM poi_subset p
    JOIN woj w
      ON ST_CONTAINS(w.geom, p.geom_point_4326)
),
woj_best AS (
    SELECT id, woj_id, dist AS dist_woj
    FROM woj_match WHERE rn = 1
),

-- ============================
-- KRAJ — 1 poligon, brak selekcji
-- ============================
kraj_best AS (
    SELECT
        p.id,
        k.kraj_id,
        ST_DISTANCE(p.geom_point_4326, ST_BOUNDARY(k.geom)) AS dist_kraj
    FROM poi_subset p
    CROSS JOIN kraj k
)

-- ============================
-- Wynik końcowy
-- ============================
SELECT
    p.id,
    g.dist_gmina,
    pw.dist_powiat,
    w.dist_woj,
    k.dist_kraj
FROM poi_subset p
LEFT JOIN gmina_best g USING (id)
LEFT JOIN powiat_best pw USING (id)
LEFT JOIN woj_best w USING (id)
LEFT JOIN kraj_best k USING (id);
