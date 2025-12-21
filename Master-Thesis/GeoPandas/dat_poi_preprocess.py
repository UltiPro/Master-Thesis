import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

# ============================
# KONFIGURACJA
# ============================

INPUT_CSV = r"C:\Users\Ultip\Desktop\mgr\dat_poi.csv"
OUTPUT_CSV = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"

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
        "osm_id": "Int64",
        "name_brand": "string",
        "name_brand_clean": "string",
        "name": "string",
        "name_clean": "string",
        "source_name": "string",
        "category": "string",
        "geom_point_4326": "string",
    },
)

t1 = time.perf_counter()
print(f"[dat_poi] Import CSV: {t1 - t0:.6f} s")

# ============================
# 2. WKT → GEOMETRY (4326)
# ============================

t2 = time.perf_counter()

df = df.dropna(subset=["geom_point_4326"]).reset_index(drop=True)
geom_4326 = gpd.GeoSeries.from_wkt(df["geom_point_4326"], crs=CRS_4326)
gdf_4326 = gpd.GeoDataFrame(df.drop(columns=["geom_point_4326"]), geometry=geom_4326)

t3 = time.perf_counter()
print(f"[dat_poi] WKT → geometry (4326): {t3 - t2:.6f} s")

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

print(f"[dat_poi] MakeValid (buffer 0): {t5 - t4:.6f} s")
print(f"[dat_poi] Invalid before: {invalid_before}, after: {invalid_after}")

# ============================
# 4. TRANSFORMACJA CRS → 2180
# ============================

t6 = time.perf_counter()

gdf_2180 = gdf_4326.to_crs(CRS_2180)

t7 = time.perf_counter()
print(f"[dat_poi] CRS transform 4326 → 2180: {t7 - t6:.6f} s")

# ============================
# 5a. INDEKS RELACYJNY (sindex)
# ============================

t8 = time.perf_counter()
_ = gdf_2180.sindex
t9 = time.perf_counter()

print(f"[dat_poi] GeoPandas sindex (Rtree): {t9 - t8:.6f} s")

# ============================
# 5b. INDEKS NEAREST (STRtree)
# ============================

t10 = time.perf_counter()

poi_geoms = list(gdf_2180.geometry.values)
poi_strtree = STRtree(poi_geoms)

t11 = time.perf_counter()
print(f"[dat_poi] STRtree (nearest): {t11 - t10:.6f} s")

# ============================
# 6. EKSPORT EPSG:2180
# ============================

t12 = time.perf_counter()

out = gdf_2180.copy()
out["geom_point_2180"] = out.geometry.to_wkt(rounding_precision=16)
out.drop(columns=["geometry"], inplace=True)

out.to_csv(OUTPUT_CSV, index=False)

t13 = time.perf_counter()
print(f"[dat_poi] Export CSV (2180): {t13 - t12:.6f} s")

print("\n[dat_poi] Preprocessing zakończony poprawnie.")
