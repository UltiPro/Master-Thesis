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
        'EPSG:4326',
        'EPSG:2180'
    ) AS geom
),
cats AS (
    SELECT DISTINCT category
    FROM dat_poi
    WHERE category IS NOT NULL
),
counts AS (
    SELECT
        c.category,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 50))      AS cnt_50m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 100))     AS cnt_100m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 500))     AS cnt_500m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 1000))    AS cnt_1000m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 5000))    AS cnt_5000m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 50000))   AS cnt_50000m,

        (SELECT COUNT(*) FROM dat_poi p, ref r
         WHERE p.category = c.category
           AND ST_DWithin(p.geom_point_2180, r.geom, 100000))  AS cnt_100000m
    FROM cats c
)
SELECT *
FROM counts
ORDER BY category;
"""

start = time.perf_counter()
df = con.execute(query).fetchdf()
elapsed = time.perf_counter() - start

print(df)
print(f"\n[Czas wykonania DuckDB – eksperyment 3]: {elapsed:.6f} s")
