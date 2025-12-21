import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
CREATE OR REPLACE TABLE feat_poi_per_admin AS
SELECT
    a.id,
    a.nazwa,
    a.typ,
    COUNT(p.id) AS poi_count
FROM geo_polska a
LEFT JOIN dat_poi p
    ON ST_Contains(a.geom_2180, p.geom_point_2180)
GROUP BY 
    a.id,
    a.nazwa,
    a.typ;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

print(f"[DuckDB – Eksperyment 7] Czas wykonania: {elapsed:.3f} s")
