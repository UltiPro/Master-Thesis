import duckdb
import time
from pathlib import Path

# ============================================
# ŚCIEŻKI DO DANYCH
# ============================================

DATA_DIR = Path(r"C:\Users\Ultip\Desktop\mgr")
EXPORT_DIR = Path(r"C:\Users\Ultip\Desktop\mgr\export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "dat_roads.csv"
OUTPUT_FILE = EXPORT_DIR / "export_osm_roads.csv"

# ============================================
# LOG WYNIKÓW CZASU
# ============================================

results = {
    "import_s": None,
    "makevalid_s": None,
    "transform_s": None,
    "export_s": None,
}

# ============================================
# DUCKDB + SPATIAL
# ============================================

con = duckdb.connect("master_thesis_duckdb.db")
con.install_extension("spatial")
con.load_extension("spatial")

# ============================================
# 1. IMPORT CSV → GEOMETRY (WKT) + FLIP
# ============================================

start = time.perf_counter()

con.execute("DROP TABLE IF EXISTS osm_roads;")

con.execute(
    f"""
    CREATE TABLE osm_roads AS
    SELECT
        id::BIGINT       AS id,
        osm_id::BIGINT   AS osm_id,
        highway::VARCHAR AS highway,

        -- WKT → GEOMETRY → FLIP (osi EPSG:4326)
        ST_FlipCoordinates(
            ST_GeomFromText(geom_line_4326)
        ) AS geom_line_4326,

        NULL::GEOMETRY AS geom_line_2180
    FROM read_csv_auto(
        '{INPUT_FILE}',
        header=True,
        max_line_size=20000000
    );
"""
)

results["import_s"] = time.perf_counter() - start
print(f"[osm_roads] Import + ST_FlipCoordinates: {results['import_s']:.3f} s")

# ============================================
# 2. ST_MakeValid (linie – warunkowo)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE osm_roads
    SET geom_line_4326 = ST_MakeValid(geom_line_4326)
    WHERE geom_line_4326 IS NOT NULL
      AND NOT ST_IsValid(geom_line_4326);
"""
)

results["makevalid_s"] = time.perf_counter() - start
print(f"[osm_roads] ST_MakeValid: {results['makevalid_s']:.3f} s")

# ============================================
# 3. TRANSFORMACJA 4326 → 2180 (PO FLIPIE)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE osm_roads
    SET geom_line_2180 = ST_Transform(
        geom_line_4326,
        'EPSG:4326',
        'EPSG:2180'
    )
    WHERE geom_line_4326 IS NOT NULL;
"""
)

results["transform_s"] = time.perf_counter() - start
print(f"[osm_roads] ST_Transform 4326->2180: {results['transform_s']:.3f} s")

# ============================================
# 3.5. INDEKSY (SPATIAL + ATRYBUTOWY)
#     - osm_roads
# ============================================

# --- indeks przestrzenny EPSG:4326 (LineString / MultiLineString)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_osm_roads_geom_4326
    ON osm_roads
    USING RTREE (geom_line_4326);
"""
)
t_4326 = time.perf_counter() - start
print(f"[osm_roads] Indeks RTREE geom_line_4326 (EPSG:4326): {t_4326:.3f} s")


# --- indeks przestrzenny EPSG:2180 (LineString / MultiLineString)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_osm_roads_geom_2180
    ON osm_roads
    USING RTREE (geom_line_2180);
"""
)
t_2180 = time.perf_counter() - start
print(f"[osm_roads] Indeks RTREE geom_line_2180 (EPSG:2180): {t_2180:.3f} s")


# --- indeks atrybutowy highway
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_osm_roads_highway
    ON osm_roads (highway);
"""
)
t_highway = time.perf_counter() - start
print(f"[osm_roads] Indeks B-tree highway: {t_highway:.3f} s")

# ============================================
# 4. EKSPORT DO CSV - tylko geometria 4326
# ============================================

start = time.perf_counter()

con.execute(
    f"""
    COPY (
        SELECT
            id,
            osm_id,
            highway,
            ST_AsText(geom_line_4326) AS geom_line_4326_wkt
        FROM osm_roads
    )
    TO '{OUTPUT_FILE}'
    (FORMAT CSV, HEADER TRUE);
"""
)

results["export_s"] = time.perf_counter() - start
print(f"[osm_roads] Export CSV (4326 only): {results['export_s']:.3f} s")

# ============================================
# PODSUMOWANIE
# ============================================

print("\n=== Wyniki preprocessing osm_roads ===")
for key, value in results.items():
    print(f"{key}: {value:.3f} s")
