import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
CREATE OR REPLACE TABLE feat_poi_border AS
WITH
gmina AS (
    SELECT
        id,
        geom_2180 AS geom,
        ST_Boundary(geom_2180) AS boundary
    FROM geo_polska
    WHERE typ = 'gmina'
),
powiat AS (
    SELECT
        id,
        geom_2180 AS geom,
        ST_Boundary(geom_2180) AS boundary
    FROM geo_polska
    WHERE typ = 'powiat'
),
woj AS (
    SELECT
        id,
        geom_2180 AS geom,
        ST_Boundary(geom_2180) AS boundary
    FROM geo_polska
    WHERE typ = 'województwo'
),
kraj AS (
    SELECT
        id,
        geom_2180 AS geom,
        ST_Boundary(geom_2180) AS boundary
    FROM geo_polska
    WHERE typ = 'kraj'
),
poi_subset AS (
    SELECT *
    FROM dat_poi
    ORDER BY id
    LIMIT 10000
)
SELECT
    p.id AS poi_id,
    ST_Distance(p.geom_point_2180, g.boundary)  AS dist_gmina,
    ST_Distance(p.geom_point_2180, pw.boundary) AS dist_powiat,
    ST_Distance(p.geom_point_2180, w.boundary)  AS dist_woj,
    ST_Distance(p.geom_point_2180, k.boundary)  AS dist_kraj
FROM poi_subset p
LEFT JOIN gmina g   ON ST_Contains(g.geom, p.geom_point_2180)
LEFT JOIN powiat pw ON ST_Contains(pw.geom, p.geom_point_2180)
LEFT JOIN woj w     ON ST_Contains(w.geom, p.geom_point_2180)
CROSS JOIN kraj k;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

print(f"[DuckDB – Eksperyment 4] Czas wykonania: {elapsed:.3f} s")
