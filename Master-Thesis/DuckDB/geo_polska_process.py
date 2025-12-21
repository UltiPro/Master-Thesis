import duckdb
import time
from pathlib import Path

# ============================================
# ŚCIEŻKI – zapisane w pamięci
# ============================================

DATA_DIR = Path(r"C:\Users\Ultip\Desktop\mgr")
EXPORT_DIR = Path(r"C:\Users\Ultip\Desktop\mgr\export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "geo_polska.csv"
OUTPUT_FILE = EXPORT_DIR / "export_geo_polska.csv"

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

con.execute("DROP TABLE IF EXISTS geo_polska;")

con.execute(
    f"""
    CREATE TABLE geo_polska AS
    SELECT
        id::INTEGER       AS id,
        typ::VARCHAR      AS typ,
        nazwa::VARCHAR    AS nazwa,
        teryt7::VARCHAR   AS teryt7,
        woj::VARCHAR      AS woj,
        pow::VARCHAR      AS pow,
        gmi::VARCHAR      AS gmi,
        rodz_gmi::VARCHAR AS rodz_gmi,

        -- WKT (lon,lat) → GEOMETRY → FLIP → (lat,lon) zgodnie z EPSG:4326
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
print(f"[geo_polska] Import + ST_FlipCoordinates: {results['import_s']:.3f} s")

# ============================================
# 2. ST_MakeValid (ZAWSZE – MultiPolygon)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE geo_polska
    SET geom_4326 = ST_MakeValid(geom_4326)
    WHERE geom_4326 IS NOT NULL;
"""
)

results["makevalid_s"] = time.perf_counter() - start
print(f"[geo_polska] ST_MakeValid (MultiPolygon): {results['makevalid_s']:.3f} s")

# ============================================
# 3. TRANSFORMACJA 4326 → 2180 (PO FLIPIE)
# ============================================

start = time.perf_counter()

con.execute(
    """
    UPDATE geo_polska
    SET geom_2180 = ST_Transform(
        geom_4326,
        'EPSG:4326',
        'EPSG:2180'
    )
    WHERE geom_4326 IS NOT NULL;
"""
)

results["transform_s"] = time.perf_counter() - start
print(f"[geo_polska] ST_Transform 4326->2180: {results['transform_s']:.3f} s")

# ============================================
# 3.5. INDEKSY (SPATIAL + ATRYBUTOWY)
#     — geo_polska
# ============================================

# --- indeks przestrzenny EPSG:4326 (MultiPolygon)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_geo_polska_geom_4326
    ON geo_polska
    USING RTREE (geom_4326);
"""
)
t_4326 = time.perf_counter() - start
print(f"[geo_polska] Indeks RTREE geom_4326 (EPSG:4326): {t_4326:.3f} s")

# --- indeks przestrzenny EPSG:2180 (MultiPolygon)
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_geo_polska_geom_2180
    ON geo_polska
    USING RTREE (geom_2180);
"""
)
t_2180 = time.perf_counter() - start
print(f"[geo_polska] Indeks RTREE geom_2180 (EPSG:2180): {t_2180:.3f} s")


# --- indeks atrybutowy typ
start = time.perf_counter()
con.execute(
    """
    CREATE INDEX idx_geo_polska_typ
    ON geo_polska (typ);
"""
)
t_typ = time.perf_counter() - start
print(f"[geo_polska] Indeks B-tree typ: {t_typ:.3f} s")

# ============================================
# 4. EKSPORT DO CSV — tylko geometria 4326
# ============================================

start = time.perf_counter()

con.execute(
    f"""
    COPY (
        SELECT
            id,
            typ,
            nazwa,
            teryt7,
            woj,
            pow,
            gmi,
            rodz_gmi,
            ST_AsText(geom_4326) AS geom_4326_wkt
        FROM geo_polska
    )
    TO '{OUTPUT_FILE}'
    (FORMAT CSV, HEADER TRUE);
"""
)

results["export_s"] = time.perf_counter() - start
print(f"[geo_polska] Export CSV (4326 only): {results['export_s']:.3f} s")

# ============================================
# PODSUMOWANIE
# ============================================

print("\n=== Wyniki preprocessing geo_polska ===")
for key, value in results.items():
    print(f"{key}: {value:.3f} s")
