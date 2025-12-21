import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
CREATE OR REPLACE TABLE geo_polska_buffer_intersection AS
WITH woj AS (
    SELECT
        id    AS woj_id,
        nazwa AS woj_name,
        geom_2180
    FROM geo_polska
    WHERE typ = 'województwo'
),
buf AS (
    SELECT
        id AS gmina_id,
        ST_Buffer(geom_2180, 5000) AS geom_buffer_5km
    FROM geo_polska
    WHERE typ = 'gmina'
)
SELECT
    b.gmina_id,
    w.woj_id,
    ST_Area(ST_Intersection(b.geom_buffer_5km, w.geom_2180)) AS area_intersection_m2,
    ST_Intersection(b.geom_buffer_5km, w.geom_2180)          AS geom_intersection
FROM buf b
JOIN woj w
    ON ST_Intersects(b.geom_buffer_5km, w.geom_2180)
WHERE ST_Intersection(b.geom_buffer_5km, w.geom_2180) IS NOT NULL;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

print(f"[DuckDB – Eksperyment 6] Czas wykonania: {elapsed:.3f} s")
