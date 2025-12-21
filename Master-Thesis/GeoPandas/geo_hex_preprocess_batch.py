import os
import time
import gc

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt
from tqdm import tqdm
from shapely.strtree import STRtree

# =====================================================
# KONFIGURACJA
# =====================================================

INPUT_CSV = r"C:\Users\Ultip\Desktop\mgr\geo_hex.csv"
OUTPUT_2180 = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180_py.csv"

CRS_4326 = "EPSG:4326"
CRS_2180 = "EPSG:2180"

BATCH_SIZE = 10_000

# =====================================================
# PRZYGOTOWANIE
# =====================================================

if os.path.exists(OUTPUT_2180):
    os.remove(OUTPUT_2180)


def now():
    return time.perf_counter()


# =====================================================
# LICZNIKI CZASU
# =====================================================

t_csv = 0.0
t_wkt = 0.0
t_makevalid = 0.0
t_crs = 0.0
t_index = 0.0
t_export = 0.0

t_wall_start = now()

# =====================================================
# 1. WCZYTANIE CAŁEJ CSV
# =====================================================

t0 = now()
df = pd.read_csv(
    INPUT_CSV,
    dtype={
        "hex_0125": "Int64",
        "teryt7": "string",
        "woj": "string",
        "pow": "string",
        "gmi": "string",
        "geom_4326": "string",
    },
)
t_csv = now() - t0
print(f"[1] Import CSV: {t_csv:.2f} s | N={len(df)}")

# =====================================================
# 2. WKT → GEOMETRY + GEODATAFRAME (CAŁOŚĆ)
# =====================================================

t0 = now()
df = df.dropna(subset=["geom_4326"]).copy()
df["geometry"] = df["geom_4326"].apply(wkt.loads)
gdf_4326 = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_4326)
t_wkt = now() - t0
print(f"[2] WKT → geometry + GeoDataFrame: {t_wkt:.2f} s")

# =====================================================
# 3. MAKE VALID – BATCHOWO
# =====================================================

t0 = now()

for i in tqdm(range(0, len(gdf_4326), BATCH_SIZE), desc="MakeValid"):
    batch = gdf_4326.iloc[i : i + BATCH_SIZE]
    mask = ~batch.geometry.is_valid
    if mask.any():
        gdf_4326.loc[batch.index[mask], "geometry"] = batch.loc[mask, "geometry"].buffer(0)

t_makevalid = now() - t0
print(f"[3] MakeValid (buffer 0): {t_makevalid:.2f} s")

# =====================================================
# 4. TRANSFORMACJA CRS 4326 → 2180 – BATCHOWO
# =====================================================

t0 = now()

gdf_2180_parts = []

for i in tqdm(range(0, len(gdf_4326), BATCH_SIZE), desc="CRS transform"):
    part = gdf_4326.iloc[i : i + BATCH_SIZE].to_crs(CRS_2180)
    gdf_2180_parts.append(part)

gdf_2180 = pd.concat(gdf_2180_parts, ignore_index=True)

t_crs = now() - t0
print(f"[4] Transformacja CRS 4326 → 2180: {t_crs:.2f} s")

# Zwalniamy 4326
del gdf_4326, gdf_2180_parts
gc.collect()

# =====================================================
# 5. INDEKSY PRZESTRZENNE (CAŁOŚĆ, EPSG:2180)
# =====================================================

# 5a. GeoPandas sindex (Rtree / STRtree backend)
t0 = now()
sindex_gp = gdf_2180.sindex
t_index_gp = now() - t0
print(f"[5a] GeoPandas sindex (EPSG:2180): {t_index_gp:.2f} s")

# 5b. Jawny STRtree (Shapely)
t0 = now()
geom_list = list(gdf_2180.geometry.values)
strtree = STRtree(geom_list)
t_index_str = now() - t0
print(f"[5b] Shapely STRtree (EPSG:2180): {t_index_str:.2f} s")


# =====================================================
# 6. EKSPORT CSV – BATCHOWO
# =====================================================

t0 = now()
header = False

for i in tqdm(range(0, len(gdf_2180), BATCH_SIZE), desc="Export CSV"):
    batch = gdf_2180.iloc[i : i + BATCH_SIZE].copy()
    batch["geom_2180"] = batch.geometry.to_wkt()
    batch.drop(columns=["geometry", "geom_4326"], inplace=True)

    batch.to_csv(
        OUTPUT_2180,
        mode="a",
        header=not header,
        index=False,
    )
    header = True

t_export = now() - t0
print(f"[6] Eksport CSV (2180): {t_export:.2f} s")

# =====================================================
# PODSUMOWANIE
# =====================================================

t_wall = now() - t_wall_start

print("------------------------------------------------------")
print(f"Łączny wall time:         {t_wall:.2f} s")
print("======================================================")
