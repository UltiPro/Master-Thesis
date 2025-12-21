import os
import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

# =========================================
# KONFIGURACJA
# =========================================

PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"
PATH_ROADS = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_roads_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# =========================================
# WCZYTYWANIE DANYCH
# =========================================


def load_hex(path):
    print("[LOAD] HEX (FULL DATASET)")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={"hex_0125": "Int64", "geom_2180": "string"},
    )
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(
        df.drop(columns=["geom_2180"]),
        geometry=geom,
    ).reset_index(drop=True)

    t2 = time.perf_counter()
    print(f"[HEX] CSV: {t1 - t0:.6f}s | WKT: {t2 - t1:.6f}s | N={len(gdf)}")

    return gdf


def load_roads(path):
    print("[LOAD] ROADS")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={
            "id": "Int64",
            "highway": "string",
            "geom_line_2180": "string",
        },
    )
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_line_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(
        df.drop(columns=["geom_line_2180"]),
        geometry=geom,
    ).reset_index(drop=True)

    t2 = time.perf_counter()
    print(f"[ROADS] CSV: {t1 - t0:.6f}s | WKT: {t2 - t1:.6f}s | N={len(gdf)}")

    return gdf


# =========================================
# EKSPERYMENT 15
# =========================================


def experiment_15_hex_road_lengths(hex_gdf, roads_gdf):
    print("\n==================== EKSPERYMENT 15 ====================")
    print("[E15] Łączna długość dróg w heksagonach")
    print("[E15] SUM(ST_Length(ST_Intersection(roads, hex)))")
    print("[E15] Indeks przestrzenny: STRtree po stronie dróg")

    # -----------------------------------------
    # Indeks przestrzenny (POZA czasem eksperymentu)
    # -----------------------------------------
    t0 = time.perf_counter()
    road_geoms = list(roads_gdf.geometry.values)
    road_tree = STRtree(road_geoms)
    t1 = time.perf_counter()
    print(f"[E15] STRtree roads build: {t1 - t0:.6f}s")

    results = []
    bbox_counts = []

    # -----------------------------------------
    # Właściwy eksperyment
    # -----------------------------------------
    t2 = time.perf_counter()

    for h in hex_gdf.itertuples(index=False):
        hex_id = int(h.hex_0125)
        hex_geom = h.geometry

        candidate_idxs = road_tree.query(hex_geom)
        bbox_counts.append(len(candidate_idxs))

        if candidate_idxs.size == 0:
            results.append(
                {
                    "hex_id": hex_id,
                    "total_road_length_m": 0.0,
                }
            )
            continue

        total_len = 0.0

        for idx in candidate_idxs:
            geom_line = road_geoms[idx]
            if geom_line.intersects(hex_geom):
                inter = geom_line.intersection(hex_geom)
                if not inter.is_empty:
                    total_len += float(inter.length)

        results.append(
            {
                "hex_id": hex_id,
                "total_road_length_m": total_len,
            }
        )

    t3 = time.perf_counter()

    print(
        f"[E15] BBox candidates – min: {min(bbox_counts)}, "
        f"max: {max(bbox_counts)}, "
        f"avg: {sum(bbox_counts)/len(bbox_counts):.2f}"
    )
    print(f"[E15] Czas eksperymentu: {t3 - t2:.6f}s")

    # -----------------------------------------
    # Zapis wyników
    # -----------------------------------------
    out = pd.DataFrame(results).sort_values("hex_id")
    out_path = os.path.join(OUT_DIR, "hex_road_lengths_py.csv")
    out.to_csv(out_path, index=False)

    print(f"[E15] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE danych do eksperymentu 15 ===")

    hex_gdf = load_hex(PATH_HEX)
    roads_gdf = load_roads(PATH_ROADS)

    experiment_15_hex_road_lengths(hex_gdf, roads_gdf)

    print("\n=== EKSPERYMENT 15 ZAKOŃCZONY ===")
