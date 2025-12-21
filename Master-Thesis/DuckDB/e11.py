import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS feat_road_longest_per_category;

CREATE TABLE feat_road_longest_per_category AS
WITH road_lengths AS (
    SELECT
        id,
        highway,
        ST_Length(geom_line_2180) AS length_m
    FROM osm_roads
),
ranked AS (
    SELECT
        highway,
        id AS road_id,
        length_m,
        ROW_NUMBER() OVER (
            PARTITION BY highway
            ORDER BY length_m DESC
        ) AS rn
    FROM road_lengths
)
SELECT
    highway,
    road_id,
    length_m
FROM ranked
WHERE rn = 1;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM feat_road_longest_per_category LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 11]: {elapsed:.6f} s")
