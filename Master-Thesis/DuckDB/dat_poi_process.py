import duckdb
import time
from pathlib import Path

# ============================================
# ŚCIEŻKI – zgodnie z ustaleniem
# ============================================

DATA_DIR = Path(r"C:\Users\Ultip\Desktop\mgr")
EXPORT_DIR = Path(r"C:\Users\Ultip\Desktop\mgr\export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "dat_poi.csv"
OUTPUT_FILE = EXPORT_DIR / "export_dat_poi.csv"

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
# 1. IMPORT CSV → GEOMETRY (WKT) + FLIP OSI
# ============================================

start = time.perf_counter()

con.execute("DROP TABLE IF EXISTS dat_poi;")

con.execute(
    f"""
    CREATE TABLE dat_poi AS
    SELECT
        id::INTEGER                    AS id,
        osm_id::BIGINT                 AS osm_id,
        name_brand::VARCHAR            AS name_brand,
        name_brand_clean::VARCHAR      AS name_brand_clean,
        name::VARCHAR                  AS name,
        name_clean::VARCHAR            AS name_clean,
        source_name::VARCHAR           AS source_name,
        category::VARCHAR              AS category,

        -- WKT (lon,lat) → GEOMETRY → FLIP → (lat,lon) zgodnie z EPSG:4326
        ST_FlipCoordinates(
            ST_GeomFromText(geom_point_4326)
        ) AS geom_point_4326,

        NULL::GEOMETRY AS geom_point_2180
    FROM read_csv_auto('{INPUT_FILE}', header=True);
"""
)

results["import_s"] = time.perf_counter() - start
print(f"[dat_poi] Import + ST_FlipCoordinates: {results['import_s']:.3f} s")

# ============================================
# 2. ST_MakeValid
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE dat_poi
    SET geom_point_4326 = ST_MakeValid(geom_point_4326)
    WHERE geom_point_4326 IS NOT NULL
      AND NOT ST_IsValid(geom_point_4326);
"""
)

results["makevalid_s"] = time.perf_counter() - start
print(f"[dat_poi] ST_MakeValid: {results['makevalid_s']:.3f} s")

# ============================================
# 3. TRANSFORMACJA 4326 → 2180 (PO FLIPIE)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE dat_poi
    SET geom_point_2180 = ST_Transform(
        geom_point_4326,
        'EPSG:4326',
        'EPSG:2180'
    )
    WHERE geom_point_4326 IS NOT NULL;
"""
)

results["transform_s"] = time.perf_counter() - start
print(f"[dat_poi] ST_Transform 4326->2180: {results['transform_s']:.3f} s")

# ============================================
# 3.5. INDEKSY (SPATIAL + ATRYBUTOWY)
#     — osobny pomiar czasu
# ============================================

# --- indeks przestrzenny EPSG:4326
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_dat_poi_geom_4326
    ON dat_poi
    USING RTREE (geom_point_4326);
"""
)
t_4326 = time.perf_counter() - start
print(f"[dat_poi] Indeks RTREE geom_point_4326 (EPSG:4326): {t_4326:.3f} s")


# --- indeks przestrzenny EPSG:2180
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_dat_poi_geom_2180
    ON dat_poi
    USING RTREE (geom_point_2180);
"""
)
t_2180 = time.perf_counter() - start
print(f"[dat_poi] Indeks RTREE geom_point_2180 (EPSG:2180): {t_2180:.3f} s")


# --- indeks atrybutowy category
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_dat_poi_category
    ON dat_poi (category);
"""
)
t_category = time.perf_counter() - start
print(f"[dat_poi] Indeks B-tree category: {t_category:.3f} s")

# ============================================
# 4. EKSPORT DO CSV — tylko geometria 4326 (WKT)
# ============================================

start = time.perf_counter()

con.execute(
    f"""
    COPY (
        SELECT
            id,
            osm_id,
            name_brand,
            name_brand_clean,
            name,
            name_clean,
            source_name,
            category,
            ST_AsText(geom_point_4326) AS geom_point_4326_wkt
        FROM dat_poi
    )
    TO '{OUTPUT_FILE}'
    (FORMAT CSV, HEADER TRUE);
"""
)

results["export_s"] = time.perf_counter() - start
print(f"[dat_poi] Export CSV (4326 only): {results['export_s']:.3f} s")

# ============================================
# PODSUMOWANIE
# ============================================

print("\n=== Wyniki preprocessing dat_poi ===")
for key, value in results.items():
    print(f"{key}: {value:.3f} s")
