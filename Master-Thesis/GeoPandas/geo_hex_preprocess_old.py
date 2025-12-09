import time
import pandas as pd
import geopandas as gpd
from shapely import wkt
import gc

# ============================
#  KONFIGURACJA
# ============================

INPUT_CSV = r"C:\\Users\\Ultip\\Desktop\\mgr\\geo_hex.csv"
OUTPUT_4326 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_hex_4326_py.csv"

CRS_4326 = "EPSG:4326"

# ============================
#  1. WCZYTANIE CSV + KONWERSJA WKT
# ============================

t00 = time.perf_counter()
df = pd.read_csv(INPUT_CSV, dtype={
    "hex_0125": "Int64",
    "teryt7": "string",
    "woj": "string",
    "pow": "string",
    "gmi": "string",
    "geom_4326": "string",
})
t01 = time.perf_counter()
print(f"[geo_hex] Wczytanie CSV: {t01 - t00:.6f} s")

# Konwersja WKT → Shapely
t10 = time.perf_counter()
df["geometry"] = df["geom_4326"].dropna().apply(wkt.loads)
gdf_4326 = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_4326)
t11 = time.perf_counter()
print(f"[geo_hex] Konwersja WKT → geometry + GeoDataFrame: {t11 - t10:.6f} s")

# ============================
#  2. MAKE VALID
# ============================

invalid_before = (~gdf_4326.geometry.is_valid).sum()
t20 = time.perf_counter()
gdf_4326.loc[~gdf_4326.geometry.is_valid, "geometry"] = \
    gdf_4326.loc[~gdf_4326.geometry.is_valid, "geometry"].buffer(0)
t21 = time.perf_counter()

invalid_after = (~gdf_4326.geometry.is_valid).sum()
print(f"[geo_hex] MakeValid: {t21 - t20:.6f} s (naprawione: {invalid_before - invalid_after})")

# ============================
#  3. INDEKS PRZESTRZENNY 4326
# ============================

t30 = time.perf_counter()
_ = gdf_4326.sindex
t31 = time.perf_counter()
print(f"[geo_hex] Indeks Rtree (4326): {t31 - t30:.6f} s")

# ============================
#  4. EKSPORT 4326
# ============================

t50 = time.perf_counter()
gdf_4326["geom_4326"] = gdf_4326.geometry.to_wkt(rounding_precision=16)
gdf_4326.drop(columns=["geometry"], inplace=True)
gdf_4326.to_csv(OUTPUT_4326, index=False)
t51 = time.perf_counter()
print(f"[geo_hex] Eksport 4326 → CSV: {t51 - t50:.6f} s")

# ZWALNIAMY PAMIĘĆ PO 4326
del gdf_4326
gc.collect()
