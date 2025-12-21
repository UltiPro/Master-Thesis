import os
import time
import pandas as pd
import numpy as np
import geopandas as gpd

from shapely.strtree import STRtree

# =====================================================
# KONFIGURACJA
# =====================================================

PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"
PATH_ROADS = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_roads_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
CRS = "EPSG:2180"

os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================
# ŁADOWANIE DANYCH
# =====================================================


def load_gdf(path, geom_col, dtype=None):
    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()
    print(f"[LOAD] CSV {os.path.basename(path)}: {t1 - t0:.6f} s")

    t2 = time.perf_counter()
    geom = gpd.GeoSeries.from_wkt(df[geom_col], crs=CRS)
    gdf = gpd.GeoDataFrame(df.drop(columns=[geom_col]), geometry=geom)
    t3 = time.perf_counter()
    print(f"[LOAD] WKT → geometry: {t3 - t2:.6f} s")

    t4 = time.perf_counter()
    _ = gdf.sindex
    t5 = time.perf_counter()
    print(f"[LOAD] sindex build: {t5 - t4:.6f} s")

    return gdf.reset_index(drop=True)


# =====================================================
# EKSPERYMENT 9
# =====================================================


def experiment_9_feat_road_avg_length(roads):
    print("\n==================== EKSPERYMENT 9 ====================")
    print("[E9] Średnia długość odcinków dróg per highway")
    print("[E9] Operacja lokalna + groupby (bez indeksów przestrzennych)")

    t0 = time.perf_counter()

    roads["length_m"] = roads.geometry.length

    out = roads.groupby("highway", observed=True)["length_m"].mean().reset_index()

    t1 = time.perf_counter()
    print(f"[E9] Liczba klas highway: {len(out)}")
    print(f"[E9] Czas eksperymentu: {t1 - t0:.6f} s")

    out.to_csv(
        os.path.join(OUT_DIR, "feat_road_avg_length_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 10
# =====================================================


def experiment_10_feat_poi_nearest_road(poi, roads):
    print("\n==================== EKSPERYMENT 10 ====================")
    print("[E10] Najbliższa droga dla każdego POI (STRtree nearest)")

    # -------------------------------------------------
    # Budowa STRtree – POZA czasem eksperymentu
    # -------------------------------------------------
    road_geoms = list(roads.geometry.values)
    tree = STRtree(road_geoms)

    # mapowanie geometry → index w roads
    geom_to_index = {geom: i for i, geom in enumerate(road_geoms)}

    rows = []

    # -------------------------------------------------
    # POMIAR CZASU EKSPERYMENTU
    # -------------------------------------------------
    t0 = time.perf_counter()

    for p in poi.itertuples(index=False):
        geom_p = p.geometry

        nearest_obj = tree.nearest(geom_p)

        # STRtree.nearest może zwrócić int lub geometrię
        if isinstance(nearest_obj, (int, np.integer)):
            road_idx = int(nearest_obj)
            road_geom = road_geoms[road_idx]
        else:
            road_geom = nearest_obj
            road_idx = geom_to_index[road_geom]

        road = roads.iloc[road_idx]
        dist = float(geom_p.distance(road_geom))

        rows.append(
            {
                "poi_id": int(p.id),
                "road_id": int(road.id),
                "distance_m": dist,
            }
        )

    t1 = time.perf_counter()

    print(f"[E10] Czas eksperymentu: {t1 - t0:.6f} s")
    print(f"[E10] Liczba wyników: {len(rows)}")

    # zapis POZA pomiarem
    pd.DataFrame(rows).to_csv(
        os.path.join(OUT_DIR, "feat_poi_nearest_road_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 11
# =====================================================


def experiment_11_feat_road_longest_per_category(roads):
    print("\n==================== EKSPERYMENT 11 ====================")
    print("[E11] Najdłuższy odcinek drogi per highway")
    print("[E11] Bez sortowania – groupby + idxmax")

    t0 = time.perf_counter()

    roads["length_m"] = roads.geometry.length

    idx = roads.groupby("highway", observed=True)["length_m"].idxmax()
    out = roads.loc[idx, ["highway", "id", "length_m"]].reset_index(drop=True)

    t1 = time.perf_counter()
    print(f"[E11] Liczba klas highway: {len(out)}")
    print(f"[E11] Czas eksperymentu: {t1 - t0:.6f} s")

    out.to_csv(
        os.path.join(OUT_DIR, "feat_road_longest_per_category_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 12
# =====================================================


def experiment_12_feat_roads_near_poi(poi, roads, radius=500, poi_limit=None):
    print("\n==================== EKSPERYMENT 12 ====================")
    print(f"[E12] Suma długości dróg w promieniu {radius} m od POI")

    # -------------------------------------------------
    # LIMIT POI (deterministyczny, jak ORDER BY id LIMIT N)
    # -------------------------------------------------
    if poi_limit is not None:
        poi_iter = poi.sort_values("id").head(poi_limit)
        print(f"[E12] LIMIT POI = {poi_limit}")
    else:
        poi_iter = poi
        print(f"[E12] POI = wszystkie ({len(poi)})")

    roads_sidx = roads.sindex
    bbox_counts = []
    rows = []

    t0 = time.perf_counter()

    for p in poi_iter.itertuples(index=False):
        buf = p.geometry.buffer(radius)

        # 1) Prefiltr BBOX przez indeks przestrzenny dróg
        idx = list(roads_sidx.intersection(buf.bounds))
        bbox_counts.append(len(idx))

        candidates = roads.iloc[idx]
        if len(candidates) == 0:
            rows.append(
                {
                    "poi_id": int(p.id),
                    "roads_length_m_500m": 0.0,
                    "n_bbox_candidates": 0,
                }
            )
            continue

        # 2) Dokładny dystans metryczny (EPSG:2180)
        dists = candidates.geometry.distance(p.geometry)
        near = candidates[dists <= radius]

        total_len = float(near.geometry.length.sum()) if len(near) > 0 else 0.0

        rows.append(
            {
                "poi_id": int(p.id),
                "roads_length_m_500m": total_len,
                "n_bbox_candidates": int(len(candidates)),
            }
        )

    t1 = time.perf_counter()

    print(
        f"[E12] BBox candidates – min: {min(bbox_counts)}, "
        f"max: {max(bbox_counts)}, "
        f"avg: {sum(bbox_counts)/len(bbox_counts):.2f}"
    )
    print(f"[E12] Czas eksperymentu: {t1 - t0:.6f} s")

    pd.DataFrame(rows).to_csv(
        os.path.join(OUT_DIR, "feat_roads_near_poi_py.csv"),
        index=False,
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("=== ŁADOWANIE DANYCH ===")

    poi = load_gdf(PATH_POI, "geom_point_2180")
    roads = load_gdf(PATH_ROADS, "geom_line_2180")

    roads["highway"] = roads["highway"].astype("category")

    experiment_9_feat_road_avg_length(roads)
    experiment_10_feat_poi_nearest_road(poi, roads)
    experiment_11_feat_road_longest_per_category(roads)
    experiment_12_feat_roads_near_poi(poi, roads, radius=500, poi_limit=100000)

    print("\n=== EKSPERYMENTY 9–12 ZAKOŃCZONE ===")
