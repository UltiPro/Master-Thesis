import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS feat_road_avg_length;

CREATE TABLE feat_road_avg_length AS
SELECT
    highway,
    AVG(ST_Length(geom_line_2180)) AS avg_length_m
FROM osm_roads
WHERE geom_line_2180 IS NOT NULL
GROUP BY highway
ORDER BY avg_length_m DESC;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM feat_road_avg_length;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 9]: {elapsed:.6f} s")
