import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.strtree import STRtree

# =========================================
# Ścieżki
# =========================================

PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"
PATH_ROADS = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_roads_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# Parametryzacja – ile hexagonów wczytać
HEX_LIMIT_E15 = 20000  # możesz testować np. 1k / 5k / 20k / 100k


# =========================================
# Wczytywanie danych
# =========================================


def load_hex_limited(path, limit):
    print(f"[LOAD] ładowanie HEX (limit={limit})")

    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype={"hex_0125": "Int64", "geom_2180": "string"}, nrows=limit)
    t1 = time.perf_counter()

    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)

    t2 = time.perf_counter()

    print(f"[HEX] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(gdf)}")
    return gdf


def load_roads(path):
    print("[LOAD] ładowanie dróg")

    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype={"id": "Int64", "highway": "string", "geom_line_2180": "string"})
    t1 = time.perf_counter()

    df["geometry"] = df["geom_line_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)

    t2 = time.perf_counter()

    print(f"[ROADS] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(gdf)}")
    return gdf


# =========================================
# EKSPERYMENT 15
# =========================================


def experiment_15_hex_road_lengths(hex_gdf, roads_gdf):
    """
    Odpowiednik Postgresa:

    SELECT
        h.hex_0125,
        SUM(ST_Length(ST_Intersection(r.geom, h.geom)))
    FROM hex h
    JOIN roads r ON ST_Intersects(...)
    GROUP BY h.hex_0125;
    """

    print("\n==================== EKSPERYMENT 15 ====================")

    # =========================================
    # STRtree dla dróg
    # =========================================

    t0 = time.perf_counter()
    road_geoms = list(roads_gdf.geometry.values)
    tree = STRtree(road_geoms)
    geom_to_index = {geom: i for i, geom in enumerate(road_geoms)}
    t1 = time.perf_counter()

    print(f"[E15] STRtree roads: {t1 - t0:.4f}s")

    results = []

    # =========================================
    # Obliczenia
    # =========================================

    t2 = time.perf_counter()

    for _, h in hex_gdf.iterrows():
        hex_id = int(h["hex_0125"])
        hex_geom = h.geometry

        # Kandydaci linii przecinających hex
        candidates = tree.query(hex_geom)

        if len(candidates) == 0:
            results.append({"hex_id": hex_id, "total_road_length_m": 0.0})
            continue

        idxs = []
        for c in candidates:
            if isinstance(c, (int, np.integer)):
                idxs.append(int(c))
            else:
                idx = geom_to_index.get(c)
                if idx is not None:
                    idxs.append(idx)

        road_subset = roads_gdf.iloc[idxs]

        total_length = 0.0

        # ST_Intersection + ST_Length
        for geom_line in road_subset.geometry:
            if not geom_line.intersects(hex_geom):
                continue

            inter = geom_line.intersection(hex_geom)
            if inter.is_empty:
                continue

            total_length += float(inter.length)

        results.append({"hex_id": hex_id, "total_road_length_m": total_length})

    t3 = time.perf_counter()

    print(f"[E15] Czas obliczeń: {t3 - t2:.4f}s")

    # =========================================
    # Zapis
    # =========================================

    out = pd.DataFrame(results).sort_values("hex_id")
    out_path = os.path.join(OUT_DIR, "hex_road_lengths_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E15] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE danych do E15 ===")

    hex_gdf = load_hex_limited(PATH_HEX, HEX_LIMIT_E15)
    roads_gdf = load_roads(PATH_ROADS)

    experiment_15_hex_road_lengths(hex_gdf, roads_gdf)

    print("\n=== EKSPERYMENT 15 ZAKOŃCZONY ===")
