import time
import pandas as pd
import geopandas as gpd
from shapely import wkt

# ============================
#  KONFIGURACJA
# ============================

INPUT_CSV = r"C:\\Users\\Ultip\\Desktop\\mgr\\dat_poi.csv"
OUTPUT_4326 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\dat_poi_4326.csv"
OUTPUT_2180 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\dat_poi_2180.csv"

CRS_4326 = "EPSG:4326"
CRS_2180 = "EPSG:2180"

# ============================
#  1. WCZYTANIE CSV + KONWERSJA WKT → GEOMETRIA 4326
# ============================

t00 = time.perf_counter()

df = pd.read_csv(
    INPUT_CSV,
    dtype={
        "id": "Int64",
        "osm_id": "Int64",
        "name_brand": "string",
        "name_brand_clean": "string",
        "name": "string",
        "name_clean": "string",
        "source_name": "string",
        "category": "string",
        "geom_wkt": "string",
    },
)

t01 = time.perf_counter()
print(f"[dat_poi] Wczytanie CSV: {t01 - t00:.6f} s")

# Konwersja WKT → Shapely geometry
t10 = time.perf_counter()
df["geometry"] = df["geom_point_4326"].dropna().apply(wkt.loads)
gdf_4326 = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_4326)
t11 = time.perf_counter()
print(f"[dat_poi] Konwersja WKT → geometry + GeoDataFrame: {t11 - t10:.6f} s")

# ============================
#  2. MAKE VALID – odpowiednik ST_MakeValid
# ============================

invalid_before = (~gdf_4326.geometry.is_valid).sum()

t20 = time.perf_counter()

# heurystyczna naprawa — buffer(0)
gdf_4326.loc[~gdf_4326.geometry.is_valid, "geometry"] = gdf_4326.loc[
    ~gdf_4326.geometry.is_valid, "geometry"
].buffer(0)

t21 = time.perf_counter()

invalid_after = (~gdf_4326.geometry.is_valid).sum()
print(f"[dat_poi] Nieprawidłowe geometrie przed MakeValid: {invalid_before}")
print(f"[dat_poi] Nieprawidłowe geometrie po MakeValid: {invalid_after}")
print(f"[dat_poi] MakeValid (buffer(0)): {t21 - t20:.6f} s")

# ============================
#  3. BUDOWA INDEKSU PRZESTRZENNEGO 4326
# ============================

t30 = time.perf_counter()
sindex_4326 = gdf_4326.sindex  # budowa R-tree
t31 = time.perf_counter()

print(f"[dat_poi] Budowa indeksu przestrzennego Rtree (4326): {t31 - t30:.6f} s")

# ============================
#  4. TRANSFORMACJA DO EPSG:2180 (ST_Transform)
# ============================

t40 = time.perf_counter()
gdf_2180 = gdf_4326.to_crs(CRS_2180)
t41 = time.perf_counter()

print(f"[dat_poi] Transformacja 4326 → 2180: {t41 - t40:.6f} s")

# ============================
#  5. EKSPORT DO CSV – WKT 4326 i 2180
# ============================

# --- Export 4326 ---
t50 = time.perf_counter()

gdf_4326["geom_point_4326"] = gdf_4326.geometry.to_wkt(rounding_precision=16)
gdf_4326.drop(columns=["geometry"], inplace=True)
gdf_4326.to_csv(OUTPUT_4326, index=False)

t51 = time.perf_counter()
print(f"[dat_poi] Eksport 4326 → CSV: {t51 - t50:.6f} s")

# --- Export 2180 ---
t60 = time.perf_counter()

gdf_2180["geom_point_2180"] = gdf_2180.geometry.to_wkt(rounding_precision=16)
gdf_2180.drop(columns=["geometry", "geom_point_4326"], errors="ignore", inplace=True)
gdf_2180.to_csv(OUTPUT_2180, index=False)

t61 = time.perf_counter()
print(f"[dat_poi] Eksport 2180 → CSV: {t61 - t60:.6f} s")
