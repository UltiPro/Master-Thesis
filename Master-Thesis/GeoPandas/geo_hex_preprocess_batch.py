import os
import time
import gc

import pandas as pd
import geopandas as gpd
from shapely import wkt
from tqdm import tqdm
import psutil

# ============================
#  KONFIGURACJA
# ============================

INPUT_CSV = r"C:\\Users\\Ultip\\Desktop\\mgr\\geo_hex.csv"
OUTPUT_4326 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_hex_4326_py.csv"
OUTPUT_2180 = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_hex_2180_py.csv"

CRS_4326 = "EPSG:4326"
CRS_2180 = "EPSG:2180"

BATCH_SIZE = 10_000

# usuwamy stare outputy
for path in (OUTPUT_4326, OUTPUT_2180):
    if os.path.exists(path):
        os.remove(path)

# ============================
#  POMOCNICZE: RAM
# ============================


def get_ram_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024**2)


# ============================
#  SUMARYCZNE LICZNIKI CZASU
# ============================

total_import = 0.0
total_wkt = 0.0
total_makevalid = 0.0
total_index = 0.0
total_crs = 0.0
total_export_4326 = 0.0
total_export_2180 = 0.0

# ============================
#  STRUMIENIOWE PRZETWARZANIE
# ============================

t_total_start = time.perf_counter()

reader_start = time.perf_counter()
reader = pd.read_csv(
    INPUT_CSV,
    chunksize=BATCH_SIZE,
    dtype={
        "hex_0125": "Int64",
        "teryt7": "string",
        "woj": "string",
        "pow": "string",
        "gmi": "string",
        "geom_4326": "string",
    },
)
reader_end = time.perf_counter()
total_import += reader_end - reader_start

header_4326 = False
header_2180 = False

print(f"[geo_hex] Start streamingowego przetwarzania...")

for batch_idx, chunk in enumerate(tqdm(reader)):

    # ====== WKT → geometry ======
    t0 = time.perf_counter()

    chunk = chunk.dropna(subset=["geom_4326"]).copy()
    gdf_4326 = gpd.GeoDataFrame(chunk, geometry=chunk["geom_4326"].apply(wkt.loads), crs=CRS_4326)

    t1 = time.perf_counter()
    total_wkt += t1 - t0

    # ====== MakeValid ======
    t0 = time.perf_counter()

    mask = ~gdf_4326.geometry.is_valid
    if mask.any():
        gdf_4326.loc[mask, "geometry"] = gdf_4326.loc[mask, "geometry"].buffer(0)

    t1 = time.perf_counter()
    total_makevalid += t1 - t0

    # ====== Export 4326 ======
    t0 = time.perf_counter()

    out = gdf_4326.copy()
    out["geom_4326"] = out.geometry.to_wkt()
    out.drop(columns=["geometry"], inplace=True)

    out.to_csv(
        OUTPUT_4326,
        mode="a",
        header=(not header_4326),
        index=False,
    )
    header_4326 = True

    t1 = time.perf_counter()
    total_export_4326 += t1 - t0

    # ====== Transformacja CRS ======
    t0 = time.perf_counter()
    gdf_2180 = gdf_4326.to_crs(CRS_2180)
    t1 = time.perf_counter()
    total_crs += t1 - t0

    # ====== Export 2180 ======
    t0 = time.perf_counter()

    out2 = gdf_2180.copy()
    out2["geom_2180"] = out2.geometry.to_wkt()
    out2.drop(columns=["geometry", "geom_4326"], inplace=True)

    out2.to_csv(
        OUTPUT_2180,
        mode="a",
        header=(not header_2180),
        index=False,
    )
    header_2180 = True

    t1 = time.perf_counter()
    total_export_2180 += t1 - t0

    # ====== cleanup ======
    del gdf_4326, gdf_2180, out, out2, chunk
    gc.collect()

t_total_end = time.perf_counter()

# ============================
#  PODSUMOWANIE
# ============================

print("\n==================== PODSUMOWANIE CZASÓW ====================")
print(f"Import CSV:                {total_import:.2f} s")
print(f"WKT → geometry:            {total_wkt:.2f} s")
print(f"MakeValid:                 {total_makevalid:.2f} s")
print(f"Transformacja CRS (2180):  {total_crs:.2f} s")
print(f"Eksport 4326:              {total_export_4326:.2f} s")
print(f"Eksport 2180:              {total_export_2180:.2f} s")
print("--------------------------------------------------------------")
print(f"Łączny czas (wall time):   {t_total_end - t_total_start:.2f} s")
print("==============================================================")
