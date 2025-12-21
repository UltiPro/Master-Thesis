import duckdb
import time
from pathlib import Path

# ============================================
# ŚCIEŻKI – zgodnie z ustaleniem
# ============================================

DATA_DIR = Path(r"C:\Users\Ultip\Desktop\mgr")
EXPORT_DIR = Path(r"C:\Users\Ultip\Desktop\mgr\export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "geo_hex.csv"
OUTPUT_FILE = EXPORT_DIR / "export_geo_hex.csv"

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
# 1. IMPORT CSV → GEOMETRY + FLIP
# ============================================

start = time.perf_counter()

con.execute("DROP TABLE IF EXISTS geo_hex;")

con.execute(
    f"""
    CREATE TABLE geo_hex AS
    SELECT
        hex_0125::BIGINT AS hex_0125,
        teryt7::VARCHAR  AS teryt7,
        woj::VARCHAR     AS woj,
        pow::VARCHAR     AS pow,
        gmi::VARCHAR     AS gmi,

        -- WKT → GEOMETRY → FLIP osi EPSG:4326
        ST_FlipCoordinates(
            ST_GeomFromText(geom_4326)
        ) AS geom_4326,

        NULL::GEOMETRY AS geom_2180
    FROM read_csv_auto(
        '{INPUT_FILE}',
        header=True,
        max_line_size=20000000
    );
"""
)

results["import_s"] = time.perf_counter() - start
print(f"[geo_hex] Import + ST_FlipCoordinates: {results['import_s']:.3f} s")

# ============================================
# 2. ST_MakeValid (POLYGONS!)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE geo_hex
    SET geom_4326 = ST_MakeValid(geom_4326)
    WHERE geom_4326 IS NOT NULL
      AND NOT ST_IsValid(geom_4326);
"""
)

results["makevalid_s"] = time.perf_counter() - start
print(f"[geo_hex] ST_MakeValid: {results['makevalid_s']:.3f} s")

# ============================================
# 3. TRANSFORMACJA 4326 → 2180
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE geo_hex
    SET geom_2180 = ST_Transform(
        geom_4326,
        'EPSG:4326',
        'EPSG:2180'
    )
    WHERE geom_4326 IS NOT NULL;
"""
)

results["transform_s"] = time.perf_counter() - start
print(f"[geo_hex] ST_Transform 4326->2180: {results['transform_s']:.3f} s")

# ============================================
# 3.5. INDEKSY PRZESTRZENNE
#     — geo_hex (tylko geometria)
# ============================================

# --- indeks przestrzenny EPSG:4326 (Polygon / MultiPolygon)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_geo_hex_geom_4326
    ON geo_hex
    USING RTREE (geom_4326);
"""
)
t_4326 = time.perf_counter() - start
print(f"[geo_hex] Indeks RTREE geom_4326 (EPSG:4326): {t_4326:.3f} s")


# --- indeks przestrzenny EPSG:2180 (Polygon / MultiPolygon)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_geo_hex_geom_2180
    ON geo_hex
    USING RTREE (geom_2180);
"""
)
t_2180 = time.perf_counter() - start
print(f"[geo_hex] Indeks RTREE geom_2180 (EPSG:2180): {t_2180:.3f} s")

# ============================================
# 4. EKSPORT — tylko geometria 4326
# ============================================

start = time.perf_counter()

con.execute(
    f"""
    COPY (
        SELECT
            hex_0125,
            teryt7,
            woj,
            pow,
            gmi,
            ST_AsText(geom_4326) AS geom_4326_wkt
        FROM geo_hex
    )
    TO '{OUTPUT_FILE}'
    (FORMAT CSV, HEADER TRUE);
"""
)

results["export_s"] = time.perf_counter() - start
print(f"[geo_hex] Export CSV (4326 only): {results['export_s']:.3f} s")

# ============================================
# PODSUMOWANIE
# ============================================

print("\n=== Wyniki preprocessing geo_hex ===")
for key, value in results.items():
    print(f"{key}: {value:.3f} s")
