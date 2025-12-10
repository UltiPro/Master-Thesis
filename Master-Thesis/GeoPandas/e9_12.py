import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.strtree import STRtree
from concurrent.futures import ThreadPoolExecutor


PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"
PATH_ROADS = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_roads_2180.csv"
OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"


def load_gdf(path, geom_col, dtype=None):
    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()

    df["geometry"] = df[geom_col].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)

    t2 = time.perf_counter()
    sindex = gdf.sindex
    t3 = time.perf_counter()

    print(f"[LOAD] CSV {os.path.basename(path)}: {t1 - t0:.6f}s")
    print(f"[LOAD] WKT → geometry: {t2 - t1:.6f}s")
    print(f"[LOAD] sindex: {t3 - t2:.6f}s")

    return gdf, (t1 - t0), (t2 - t1), (t3 - t2)


def chunk_gdf(gdf, num_chunks):
    n = len(gdf)
    size = (n + num_chunks - 1) // num_chunks
    return [gdf.iloc[i : i + size] for i in range(0, n, size)]


# =============================
# E9
# =============================
def experiment_9_feat_road_avg_length(roads):
    print("\n==================== EKSPERYMENT 9 ====================")
    t0 = time.perf_counter()

    roads["length_m"] = roads.geometry.length
    out = (
        roads.groupby("highway")["length_m"].mean().reset_index().sort_values("length_m", ascending=False)
    )

    t1 = time.perf_counter()
    print(f"[E9] Czas obliczeń: {t1 - t0:.6f}s")

    out_path = os.path.join(OUT_DIR, "feat_road_avg_length_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E9] Zapisano: {out_path}")


# =============================
# E10 – MULTIWORKER
# =============================


def _worker_e10(chunk, roads, road_geoms, tree):
    rows = []

    for p in chunk.itertuples(index=False):
        geom_p = p.geometry

        # ---- POBIERANIE NAJBLIŻSZEGEO (jak <-> w PostGIS) ----
        nearest_obj = tree.nearest(geom_p)

        # STRtree.nearest potrafi zwracać różne typy:
        # - int (index)
        # - geometry
        # - list/ndarray
        if isinstance(nearest_obj, (list, np.ndarray)):
            nearest_obj = nearest_obj[0]

        # Jeśli int → to index
        if isinstance(nearest_obj, (int, np.integer)):
            road_idx = int(nearest_obj)
            nearest_geom = road_geoms[road_idx]
        else:
            # wynik jest geometrią → musimy znaleźć index
            nearest_geom = nearest_obj
            road_idx = road_geoms.index(nearest_geom)

        r = roads.iloc[road_idx]

        dist = geom_p.distance(nearest_geom)

        rows.append({"poi_id": int(p.id), "road_id": int(r.id), "distance_m": float(dist)})

    return rows


def experiment_10_feat_poi_nearest_road(poi, roads, num_workers=1):
    print("\n==================== EKSPERYMENT 10 (MULTI – POPRAWIONE v2) ====================")

    road_geoms = list(roads.geometry.values)
    tree = STRtree(road_geoms)

    chunks = chunk_gdf(poi, num_workers)
    results = []

    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(_worker_e10, chunk, roads, road_geoms, tree) for chunk in chunks]
        for f in futures:
            results.extend(f.result())

    t1 = time.perf_counter()
    print(f"[E10] Czas obliczeń (workers={num_workers}): {t1 - t0:.6f}s")
    print(f"[E10] Liczba wyników: {len(results)} (POI={len(poi)})")

    out = pd.DataFrame(results)
    out_path = os.path.join(OUT_DIR, "feat_poi_nearest_road_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E10] Zapisano: {out_path}")


# =============================
# E11
# =============================
def experiment_11_feat_road_longest_per_category(roads):
    print("\n==================== EKSPERYMENT 11 ====================")
    t0 = time.perf_counter()

    roads["length_m"] = roads.geometry.length
    out = (
        roads.sort_values(["highway", "length_m"], ascending=[True, False])
        .groupby("highway")
        .head(1)[["highway", "id", "length_m"]]
        .reset_index(drop=True)
    )

    t1 = time.perf_counter()
    print(f"[E11] Czas obliczeń: {t1 - t0:.6f}s")

    out_path = os.path.join(OUT_DIR, "feat_road_longest_per_category_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E11] Zapisano: {out_path}")


# =============================
# E12 – MULTIWORKER
# =============================
def _worker_e12(chunk, roads_geom, tree, geom_to_index):
    rows = []
    for _, p in chunk.iterrows():
        geom_p = p.geometry
        candidates = tree.query(geom_p.buffer(500))

        if len(candidates) == 0:
            rows.append({"poi_id": int(p["id"]), "roads_length_m_500m": 0.0})
            continue

        cand_idx = []
        for c in candidates:
            if isinstance(c, (int, np.integer)):
                cand_idx.append(int(c))
            else:
                idx = geom_to_index.get(c)
                if idx is not None:
                    cand_idx.append(idx)

        subset = roads_geom.iloc[cand_idx]
        subset = subset[subset.geometry.distance(geom_p) <= 500]

        total_len = float(subset.geometry.length.sum()) if len(subset) > 0 else 0.0
        rows.append({"poi_id": int(p["id"]), "roads_length_m_500m": total_len})

    return rows


def experiment_12_feat_roads_near_poi(poi, roads, sample_size=50000, num_workers=1):
    print("\n==================== EKSPERYMENT 12 (MULTI) ====================")

    poi_sample = poi.sort_values("id").head(sample_size).copy()
    roads_geom = roads.copy()
    tree = STRtree(list(roads_geom.geometry.values))
    geom_to_index = {geom: i for i, geom in enumerate(roads_geom.geometry.values)}

    chunks = np.array_split(poi_sample, num_workers)
    results = []

    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(_worker_e12, chunk, roads_geom, tree, geom_to_index) for chunk in chunks]
        for f in futures:
            results.extend(f.result())

    t1 = time.perf_counter()
    print(f"[E12] Czas obliczeń (workers={num_workers}): {t1 - t0:.6f}s")

    out = pd.DataFrame(results)
    out_path = os.path.join(OUT_DIR, "feat_roads_near_poi_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E12] Zapisano: {out_path}")


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    print("=== ŁADOWANIE danych ===")

    poi, poi_csv, poi_wkt, poi_sidx = load_gdf(PATH_POI, "geom_point_2180")
    roads, r_csv, r_wkt, r_sidx = load_gdf(PATH_ROADS, "geom_line_2180")

    print("\n=== PODSUMOWANIE ===")
    print(f"POI: CSV={poi_csv:.6f}s, WKT={poi_wkt:.6f}s, sindex={poi_sidx:.6f}s")
    print(f"ROADS: CSV={r_csv:.6f}s, WKT={r_wkt:.6f}s, sindex={r_sidx:.6f}s")

    # experiment_9_feat_road_avg_length(roads)
    experiment_10_feat_poi_nearest_road(poi, roads, num_workers=1)
    # experiment_11_feat_road_longest_per_category(roads)
    # experiment_12_feat_roads_near_poi(poi, roads, sample_size=50000, num_workers=1)

    print("\n=== EKSPERYMENTY 9–12 ZAKOŃCZONE ===")
