import time
import pandas as pd
import geopandas as gpd
from shapely import wkt

# ============================
#  KONFIGURACJA
# ============================

INPUT_CSV = r"C:\\Users\\Ultip\\Desktop\\mgr\\geo_polska.csv"
OUTPUT_4326 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_polska_4326.csv"
OUTPUT_2180 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_polska_2180.csv"

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
        "typ": "string",
        "nazwa": "string",
        "teryt7": "string",
        "woj": "string",
        "pow": "string",
        "gmi": "string",
        "rodz_gmi": "string",
        "geom_4326": "string",
    },
)

t01 = time.perf_counter()
print(f"[geo_polska] Wczytanie CSV: {t01 - t00:.6f} s")

# Konwersja WKT → Shapely geometry
t10 = time.perf_counter()
df["geometry"] = df["geom_4326"].dropna().apply(wkt.loads)
gdf_4326 = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_4326)
t11 = time.perf_counter()

print(f"[geo_polska] Konwersja WKT → geometry + GeoDataFrame: {t11 - t10:.6f} s")

# ============================
#  2. MAKE VALID
# ============================

invalid_before = (~gdf_4326.geometry.is_valid).sum()

t20 = time.perf_counter()
gdf_4326.loc[~gdf_4326.geometry.is_valid, "geometry"] = gdf_4326.loc[
    ~gdf_4326.geometry.is_valid, "geometry"
].buffer(0)
t21 = time.perf_counter()

invalid_after = (~gdf_4326.geometry.is_valid).sum()

print(f"[geo_polska] Nieprawidłowe geometrie przed MakeValid: {invalid_before}")
print(f"[geo_polska] Nieprawidłowe geometrie po MakeValid: {invalid_after}")
print(f"[geo_polska] MakeValid (buffer(0)): {t21 - t20:.6f} s")

# ============================
#  3. INDEKS PRZESTRZENNY 4326
# ============================

t30 = time.perf_counter()
sindex_4326 = gdf_4326.sindex
t31 = time.perf_counter()

print(f"[geo_polska] Indeks Rtree (4326): {t31 - t30:.6f} s")

# ============================
#  4. TRANSFORMACJA DO 2180
# ============================

t40 = time.perf_counter()
gdf_2180 = gdf_4326.to_crs(CRS_2180)
t41 = time.perf_counter()

print(f"[geo_polska] Transformacja 4326 → 2180: {t41 - t40:.6f} s")

# ============================
#  5. EKSPORT
# ============================

# --- Export 4326 ---
t60 = time.perf_counter()

gdf_4326["geom_4326"] = gdf_4326.geometry.to_wkt(rounding_precision=16)
gdf_4326.drop(columns=["geometry"], inplace=True)
gdf_4326.to_csv(OUTPUT_4326, index=False)

t61 = time.perf_counter()
print(f"[geo_polska] Eksport 4326 → CSV: {t61 - t60:.6f} s")

# --- Export 2180 ---
t70 = time.perf_counter()

gdf_2180["geom_2180"] = gdf_2180.geometry.to_wkt(rounding_precision=16)
gdf_2180.drop(columns=["geometry", "geom_2180"], errors="ignore", inplace=True)
gdf_2180.to_csv(OUTPUT_2180, index=False)

t71 = time.perf_counter()
print(f"[geo_polska] Eksport 2180 → CSV: {t71 - t70:.6f} s")
