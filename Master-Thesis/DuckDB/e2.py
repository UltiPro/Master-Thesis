import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
WITH ref AS (
    SELECT ST_Transform(
        ST_FlipCoordinates(
            ST_Point(19.46701915338524, 51.74357018348951)
        ),
        'EPSG:4326', 'EPSG:2180'
    ) AS geom
),
cats AS (
    SELECT DISTINCT category
    FROM dat_poi
    WHERE category IS NOT NULL
),
nearest AS (
    SELECT
        c.category,
        nn.id AS nearest_poi_id,
        nn.dist_m AS distance_m
    FROM cats c
    CROSS JOIN ref r
    CROSS JOIN LATERAL (
        SELECT
            id,
            ST_Distance(geom_point_2180, r.geom) AS dist_m
        FROM dat_poi
        WHERE category = c.category
        ORDER BY dist_m
        LIMIT 1
    ) nn
)
SELECT *
FROM nearest;
"""

start = time.perf_counter()
df = con.execute(query).fetchdf()
elapsed = time.perf_counter() - start

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 2]: {elapsed:.6f} s")
