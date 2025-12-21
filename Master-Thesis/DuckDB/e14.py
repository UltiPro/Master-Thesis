import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS vw_hex_poi_counts;

CREATE TABLE vw_hex_poi_counts AS
SELECT
    h.hex_0125,
    COUNT(p.id) AS poi_count
FROM geo_hex h
LEFT JOIN dat_poi p
    ON ST_Contains(h.geom_2180, p.geom_point_2180)
GROUP BY h.hex_0125;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM vw_hex_poi_counts LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 14]: {elapsed:.2f} s")
