import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.strtree import STRtree

# =========================================
# ŚCIEŻKI
# =========================================

PATH_HEX = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_hex_2180.csv"
PATH_POI = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\dat_poi_2180.csv"

OUT_DIR = r"C:\\Users\\Ultip\\Desktop\\mgr\\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# Parametryzacja – ile hexów wczytać
HEX_LIMIT_E14 = 200000


# =========================================
# FUNKCJE WCZYTYWANIA
# =========================================


def load_hex_limited(path, limit):
    print(f"[LOAD] ładowanie hexów LIMIT={limit}")

    t0 = time.perf_counter()
    df = pd.read_csv(path, nrows=limit, dtype={"hex_0125": "Int64", "geom_2180": "string"})
    t1 = time.perf_counter()

    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)
    t2 = time.perf_counter()

    print(f"[HEX] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(gdf)}")
    return gdf


def load_poi(path):
    print("[LOAD] ładowanie POI")

    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype={"id": "Int64", "geom_point_2180": "string"})
    t1 = time.perf_counter()

    df["geometry"] = df["geom_point_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)
    t2 = time.perf_counter()

    print(f"[POI] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(gdf)}")
    return gdf


# =========================================
# EKSPERYMENT 14 – HEX POI COUNTS
# =========================================


def experiment_14_hex_poi_counts(hex_gdf, poi_gdf):
    """
    Odpowiednik Postgresowego:

    SELECT h.hex_0125, COUNT(p.id)
    FROM geo_hex h
    LEFT JOIN dat_poi p ON ST_Contains(h.geom, p.geom)
    GROUP BY h.hex_0125;
    """

    print("\n==================== EKSPERYMENT 14 ====================")

    # Budujemy STRtree z POI
    t0 = time.perf_counter()
    poi_geoms = list(poi_gdf.geometry.values)
    poi_tree = STRtree(poi_geoms)
    geom_to_idx = {geom: i for i, geom in enumerate(poi_geoms)}
    t1 = time.perf_counter()
    print(f"[E14] STRtree POI: {t1 - t0:.4f}s")

    results = []

    t2 = time.perf_counter()

    # Przetwarzanie hexów
    for _, h in hex_gdf.iterrows():
        hex_geom = h.geometry

        # Kandydaci POI, które są potencjalnie w hexie
        candidates = poi_tree.query(hex_geom)

        if len(candidates) == 0:
            results.append({"hex_0125": int(h["hex_0125"]), "poi_count": 0})
            continue

        candidate_idx = []
        for c in candidates:
            if isinstance(c, (int, np.integer)):
                candidate_idx.append(int(c))
            else:
                idx = geom_to_idx.get(c)
                if idx is not None:
                    candidate_idx.append(idx)

        # Finalne sprawdzenie ST_Contains
        poi_subset = poi_gdf.iloc[candidate_idx]
        inside = poi_subset.geometry.within(hex_geom)

        count_inside = int(inside.sum())

        results.append({"hex_0125": int(h["hex_0125"]), "poi_count": count_inside})

    t3 = time.perf_counter()
    print(f"[E14] Czas obliczeń: {t3 - t2:.4f}s")

    # Zapis CSV
    out = pd.DataFrame(results).sort_values("hex_0125")
    path_out = os.path.join(OUT_DIR, "hex_poi_counts_py.csv")
    out.to_csv(path_out, index=False)

    print(f"[E14] Zapisano: {path_out}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE danych do eksperymentu 14 ===")

    hex_gdf = load_hex_limited(PATH_HEX, HEX_LIMIT_E14)
    poi_gdf = load_poi(PATH_POI)

    experiment_14_hex_poi_counts(hex_gdf, poi_gdf)

    print("\n=== EKSPERYMENT 14 ZAKOŃCZONY ===")
