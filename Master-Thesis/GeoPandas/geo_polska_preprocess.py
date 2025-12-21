import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

# ============================
# KONFIGURACJA
# ============================

INPUT_CSV = r"C:\Users\Ultip\Desktop\mgr\geo_polska.csv"
OUTPUT_CSV = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"

CRS_4326 = "EPSG:4326"
CRS_2180 = "EPSG:2180"

# ============================
# 1. IMPORT CSV
# ============================

t0 = time.perf_counter()

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

t1 = time.perf_counter()
print(f"[geo_polska] Import CSV: {t1 - t0:.6f} s")

# ============================
# 2. WKT → GEOMETRY (4326)
# ============================

t2 = time.perf_counter()

df = df.dropna(subset=["geom_4326"]).reset_index(drop=True)
geom_4326 = gpd.GeoSeries.from_wkt(df["geom_4326"], crs=CRS_4326)
gdf_4326 = gpd.GeoDataFrame(df.drop(columns=["geom_4326"]), geometry=geom_4326)

t3 = time.perf_counter()
print(f"[geo_polska] WKT → geometry (4326): {t3 - t2:.6f} s")

# ============================
# 3. MAKE VALID (buffer(0))
# ============================

invalid_before = (~gdf_4326.geometry.is_valid).sum()

t4 = time.perf_counter()

mask = ~gdf_4326.geometry.is_valid
if mask.any():
    gdf_4326.loc[mask, "geometry"] = gdf_4326.loc[mask, "geometry"].buffer(0)

t5 = time.perf_counter()

invalid_after = (~gdf_4326.geometry.is_valid).sum()

print(f"[geo_polska] MakeValid (buffer 0): {t5 - t4:.6f} s")
print(f"[geo_polska] Invalid before: {invalid_before}, after: {invalid_after}")

# ============================
# 4. TRANSFORMACJA CRS → 2180
# ============================

t6 = time.perf_counter()

gdf_2180 = gdf_4326.to_crs(CRS_2180)

t7 = time.perf_counter()
print(f"[geo_polska] CRS transform 4326 → 2180: {t7 - t6:.6f} s")

# ============================
# 5a. INDEKS RELACYJNY (GeoPandas sindex)
# ============================

t8 = time.perf_counter()
_ = gdf_2180.sindex
t9 = time.perf_counter()

print(f"[geo_polska] GeoPandas sindex (Rtree): {t9 - t8:.6f} s")

# ============================
# 5b. INDEKS NEAREST / RĘCZNY (STRtree)
# ============================

t10 = time.perf_counter()

polska_geoms = list(gdf_2180.geometry.values)
polska_strtree = STRtree(polska_geoms)

t11 = time.perf_counter()
print(f"[geo_polska] STRtree (manual spatial ops): {t11 - t10:.6f} s")

# ============================
# 6. EKSPORT EPSG:2180
# ============================

t12 = time.perf_counter()

out = gdf_2180.copy()
out["geom_2180"] = out.geometry.to_wkt(rounding_precision=16)
out.drop(columns=["geometry"], inplace=True)

out.to_csv(OUTPUT_CSV, index=False)

t13 = time.perf_counter()
print(f"[geo_polska] Export CSV (2180): {t13 - t12:.6f} s")

print("\n[geo_polska] Preprocessing zakończony poprawnie.")
