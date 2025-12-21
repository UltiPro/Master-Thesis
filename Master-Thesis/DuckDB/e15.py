import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
DROP TABLE IF EXISTS vw_hex_road_lengths;

CREATE TABLE vw_hex_road_lengths AS
SELECT
    h.hex_0125 AS hex_id,
    SUM(
        ST_Length(
            ST_Intersection(
                r.geom_line_2180,
                h.geom_2180
            )
        )
    ) AS total_road_length_m
FROM geo_hex h
JOIN osm_roads r
    ON ST_Intersects(
        r.geom_line_2180,
        h.geom_2180
    )
GROUP BY h.hex_0125;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

df = con.execute("SELECT * FROM vw_hex_road_lengths LIMIT 10;").fetchdf()

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 15]: {elapsed:.2f} s")
