import time
import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.strtree import STRtree
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# =========================================
# KONFIGURACJA
# =========================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"
OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"

N_THREADS_E7 = 4  # ustalone wcześniej


# =========================================
# FUNKCJA ŁADOWANIA GDF Z POMIAREM CZASU
# =========================================


def load_gdf(path, geom_col, crs="EPSG:2180", dtype=None):
    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()

    print(f"[LOAD] CSV {os.path.basename(path)}: {t1 - t0:.6f} s")

    t2 = time.perf_counter()
    df["geometry"] = df[geom_col].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=crs)
    t3 = time.perf_counter()

    print(f"[LOAD] WKT → geometry: {t3 - t2:.6f} s")

    return gdf


# =========================================
# EKSPERYMENT 7 — WERSJA 1 (single-core)
# =========================================


def experiment_7_single(geo_polska: gpd.GeoDataFrame, poi: gpd.GeoDataFrame):

    print("\n==================== EKSPERYMENT 7 (single-core) ====================")

    admin = (
        geo_polska[geo_polska["typ"].isin(["kraj", "województwo", "powiat", "gmina"])]
        .copy()
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------
    # 1. STRtree + pomiar czasu budowy indeksu
    # ---------------------------------------------------------
    poi_geoms = list(poi.geometry.values)

    t_idx0 = time.perf_counter()
    poi_tree = STRtree(poi_geoms)
    t_idx1 = time.perf_counter()

    print(f"[E7 single-core] STRtree build: {t_idx1 - t_idx0:.6f} s")

    # mapowanie geometrii na index
    geom_to_idx = {geom: i for i, geom in enumerate(poi_geoms)}

    rows = []

    t0 = time.perf_counter()

    for _, a in admin.iterrows():
        geom_a = a.geometry

        candidates = poi_tree.query(geom_a)

        if len(candidates) == 0:
            cnt = 0
        else:
            idxs = []
            for c in candidates:
                if isinstance(c, (int, np.integer)):
                    idxs.append(int(c))
                else:
                    idx = geom_to_idx.get(c)
                    if idx is not None:
                        idxs.append(idx)

            if idxs:
                subset = poi.iloc[idxs]
                mask = subset.geometry.within(geom_a)
                cnt = int(mask.sum())
            else:
                cnt = 0

        rows.append(
            {"admin_id": int(a["id"]), "admin_name": a["nazwa"], "admin_type": a["typ"], "poi_count": cnt}
        )

    t1 = time.perf_counter()
    print(f"[E7 single-core] Czas obliczeń: {t1 - t0:.6f} s")

    out = pd.DataFrame(rows)

    type_order = {"kraj": 1, "województwo": 2, "powiat": 3, "gmina": 4}
    out["type_order"] = out["admin_type"].map(type_order)
    out = out.sort_values(["type_order", "admin_id"]).drop(columns=["type_order"])

    out_path = os.path.join(OUT_DIR, "feat_poi_per_admin_single_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E7 single-core] Zapisano: {out_path}")


# =========================================
# EKSPERYMENT 7 — WERSJA 2 (multithread 4×)
# =========================================


def experiment_7_multithread(geo_polska: gpd.GeoDataFrame, poi: gpd.GeoDataFrame):

    print("\n==================== EKSPERYMENT 7 (multithread 4×) ====================")

    admin = (
        geo_polska[geo_polska["typ"].isin(["kraj", "województwo", "powiat", "gmina"])]
        .copy()
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------
    # 1. STRtree + pomiar czasu budowy indeksu
    # ---------------------------------------------------------
    poi_geoms = list(poi.geometry.values)

    t_idx0 = time.perf_counter()
    poi_tree = STRtree(poi_geoms)
    t_idx1 = time.perf_counter()

    print(f"[E7 multithread] STRtree build: {t_idx1 - t_idx0:.6f} s")

    geom_to_idx = {geom: i for i, geom in enumerate(poi_geoms)}

    def worker(a):
        geom_a = a.geometry

        candidates = poi_tree.query(geom_a)

        if len(candidates) == 0:
            cnt = 0
        else:
            idxs = []
            for c in candidates:
                if isinstance(c, (int, np.integer)):
                    idxs.append(int(c))
                else:
                    idx = geom_to_idx.get(c)
                    if idx is not None:
                        idxs.append(idx)

            if idxs:
                subset = poi.iloc[idxs]
                mask = subset.geometry.within(geom_a)
                cnt = int(mask.sum())
            else:
                cnt = 0

        return {
            "admin_id": int(a["id"]),
            "admin_name": a["nazwa"],
            "admin_type": a["typ"],
            "poi_count": cnt,
        }

    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=N_THREADS_E7) as ex:
        results = list(ex.map(worker, [row for _, row in admin.iterrows()]))

    t1 = time.perf_counter()
    print(f"[E7 multithread] Czas obliczeń: {t1 - t0:.6f} s")

    out = pd.DataFrame(results)

    type_order = {"kraj": 1, "województwo": 2, "powiat": 3, "gmina": 4}
    out["type_order"] = out["admin_type"].map(type_order)
    out = out.sort_values(["type_order", "admin_id"]).drop(columns=["type_order"])

    out_path = os.path.join(OUT_DIR, "feat_poi_per_admin_multithread_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E7 multithread] Zapisano: {out_path}")


# =========================================
# GŁÓWNY FLOW – tylko eksperyment 7
# =========================================

if __name__ == "__main__":

    print("=== Ładowanie geo_polska_2180 ===")
    geo_polska = load_gdf(PATH_POLSKA, "geom_2180")

    print("=== Ładowanie dat_poi_2180 ===")
    poi = load_gdf(PATH_POI, "geom_point_2180")

    # uruchamiamy oba warianty
    experiment_7_single(geo_polska, poi)
    experiment_7_multithread(geo_polska, poi)

    print("\n=== EKSPERYMENT 7 ZAKOŃCZONY ===")
