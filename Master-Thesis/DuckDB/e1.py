import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.install_extension("spatial")
con.load_extension("spatial")

start = time.perf_counter()

result = con.execute(
    """
    WITH ref AS (
        SELECT ST_Transform(
            ST_FlipCoordinates(
                ST_Point(19.46701915338524, 51.74357018348951)
            ),
            'EPSG:4326',
            'EPSG:2180'
        ) AS geom
    )
    SELECT p.*
    FROM dat_poi p, ref r
    ORDER BY ST_Distance(p.geom_point_2180, r.geom)
    LIMIT 1;
"""
).fetchdf()

elapsed = time.perf_counter() - start

print(result)
print(f"\n[Czas wykonania DuckDB – eksperyment 1]: {elapsed:.6f} s")
