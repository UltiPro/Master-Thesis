import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS feat_poi_nearest_road;

CREATE TABLE feat_poi_nearest_road AS
SELECT
    p.id AS poi_id,
    r.id AS road_id,
    r.dist_m AS distance_m
FROM dat_poi p
JOIN LATERAL (
    SELECT
        id,
        ST_Distance(p.geom_point_2180, geom_line_2180) AS dist_m
    FROM osm_roads
    WHERE geom_line_2180 IS NOT NULL
      AND ST_DWithin(
          p.geom_point_2180,
          geom_line_2180,
          500
      )
    ORDER BY dist_m
    LIMIT 1
) r ON TRUE
ORDER BY p.id;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM feat_poi_nearest_road LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 10 (≤500 m)]: {elapsed:.6f} s")
