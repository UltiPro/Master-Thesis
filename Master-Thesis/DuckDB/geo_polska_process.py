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
# 1. IMPORT CSV → GEOMETRY (WKT)
# ============================================

start = time.perf_counter()

con.execute("DROP TABLE IF EXISTS geo_polska;")

con.execute(f"""
    CREATE TABLE geo_polska AS
    SELECT
        id::INTEGER               AS id,
        typ::VARCHAR              AS typ,
        nazwa::VARCHAR            AS nazwa,
        teryt7::VARCHAR           AS teryt7,
        woj::VARCHAR              AS woj,
        pow::VARCHAR              AS pow,
        gmi::VARCHAR              AS gmi,
        rodz_gmi::VARCHAR         AS rodz_gmi,

        -- geom_4326 z CSV zawiera WKT
        ST_GeomFromText(geom_4326) AS geom_4326,
        NULL::GEOMETRY            AS geom_2180
    FROM read_csv_auto('{INPUT_FILE}',
        header=True,
        max_line_size=20000000
    );
""")

results["import_s"] = time.perf_counter() - start
print(f"[geo_polska] Import (CSV WKT -> GEOMETRY): {results['import_s']:.3f} s")

# ============================================
# 2. ST_MakeValid (naprawa geometrii)
# ============================================

start = time.perf_counter()

con.execute("""
    UPDATE geo_polska
    SET geom_4326 = ST_MakeValid(geom_4326)
    WHERE geom_4326 IS NOT NULL
      AND NOT ST_IsValid(geom_4326);
""")

results["makevalid_s"] = time.perf_counter() - start
print(f"[geo_polska] ST_MakeValid: {results['makevalid_s']:.3f} s")

# ============================================
# 3. TRANSFORMACJA 4326 → 2180 (PROJ)
# ============================================

start = time.perf_counter()

con.execute("""
    UPDATE geo_polska
    SET geom_2180 = ST_Transform(
        geom_4326,
        'EPSG:4326',
        'EPSG:2180'
    )
    WHERE geom_4326 IS NOT NULL;
""")

results["transform_s"] = time.perf_counter() - start
print(f"[geo_polska] ST_Transform 4326->2180: {results['transform_s']:.3f} s")

# ============================================
# 4. EKSPORT DO CSV — tylko geometria 4326
# ============================================

start = time.perf_counter()

con.execute(f"""
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
""")

results["export_s"] = time.perf_counter() - start
print(f"[geo_polska] Export CSV (4326 only): {results['export_s']:.3f} s")

# ============================================
# PODSUMOWANIE
# ============================================

print("\n=== Wyniki preprocessing geo_polska ===")
for key, value in results.items():
    print(f"{key}: {value:.3f} s")
