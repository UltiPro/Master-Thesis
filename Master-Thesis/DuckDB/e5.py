import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
CREATE OR REPLACE TABLE geo_polska_geom_features AS
SELECT
    id,
    nazwa,
    typ,
    ST_Area(geom_2180)      AS area_m2,
    ST_Perimeter(geom_2180) AS perimeter_m,
    ST_Centroid(geom_2180)  AS centroid_2180
FROM geo_polska
ORDER BY id;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

print(f"[DuckDB – Eksperyment 5] Czas wykonania: {elapsed:.6f} s")
