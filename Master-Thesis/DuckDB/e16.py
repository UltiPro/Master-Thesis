import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS geo_hex_woj_join;

CREATE TABLE geo_hex_woj_join AS
WITH woj AS (
    SELECT 
        id AS woj_id,
        nazwa AS woj_name,
        geom_2180
    FROM geo_polska
    WHERE typ = 'województwo'
),
hex_sample AS (
    SELECT 
        hex_0125 AS hex_id,
        geom_2180
    FROM geo_hex
    ORDER BY hex_0125
    LIMIT 1000
),
intersections AS (
    SELECT
        h.hex_id,
        w.woj_id,
        h.geom_2180 AS hex_geom,
        ST_Intersection(h.geom_2180, w.geom_2180) AS geom_inter
    FROM hex_sample h
    JOIN woj w
      ON ST_Intersects(h.geom_2180, w.geom_2180)
)
SELECT
    hex_id,
    woj_id,
    ST_Area(hex_geom) AS area_hex_m2,
    ST_Area(geom_inter) AS area_intersection_m2
FROM intersections
WHERE NOT ST_IsEmpty(geom_inter)
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM geo_hex_woj_join LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 16]: {elapsed:.6f} s")
