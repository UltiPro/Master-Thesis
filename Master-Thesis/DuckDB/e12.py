import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS feat_roads_near_poi;

CREATE TABLE feat_roads_near_poi AS
WITH poi_sample AS (
    SELECT
        id,
        geom_point_2180
    FROM dat_poi
    ORDER BY id
    LIMIT 1000
)
SELECT
    p.id AS poi_id,
    SUM(ST_Length(r.geom_line_2180)) AS roads_length_m_500m
FROM poi_sample p
JOIN osm_roads r
    ON ST_DWithin(
        p.geom_point_2180,
        r.geom_line_2180,
        500
    )
GROUP BY p.id
ORDER BY p.id;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM feat_roads_near_poi LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 12]: {elapsed:.6f} s")
