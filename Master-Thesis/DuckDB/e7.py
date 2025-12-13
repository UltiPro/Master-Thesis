import duckdb
import time

con = duckdb.connect("master_thesis_duckdb.db")
con.execute("INSTALL spatial; LOAD spatial;")

query = """
CREATE OR REPLACE TABLE feat_poi_per_admin AS
WITH admin_units AS (
    SELECT 
        id    AS admin_id,
        nazwa AS admin_name,
        typ   AS admin_type,
        geom_2180
    FROM geo_polska
    WHERE typ IN ('kraj', 'województwo', 'powiat', 'gmina')
)
SELECT
    a.admin_id,
    a.admin_name,
    a.admin_type,
    COUNT(p.id) AS poi_count
FROM admin_units a
LEFT JOIN dat_poi p
    ON ST_Contains(a.geom_2180, p.geom_point_2180)
GROUP BY 
    a.admin_id, 
    a.admin_name, 
    a.admin_type
ORDER BY 
    CASE a.admin_type
        WHEN 'kraj' THEN 1
        WHEN 'województwo' THEN 2
        WHEN 'powiat' THEN 3
        WHEN 'gmina' THEN 4
    END,
    a.admin_id;
"""

start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start

print(f"[DuckDB – Eksperyment 7] Czas wykonania: {elapsed:.3f} s")
