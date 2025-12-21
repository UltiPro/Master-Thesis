import os
import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

# =========================================
# KONFIGURACJA
# =========================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"
HEX_LIMIT_E16 = 1000000

# =========================================
# WCZYTYWANIE DANYCH
# =========================================


def load_woj(path):
    print("[LOAD] geo_polska → województwa")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={
            "id": "Int64",
            "typ": "string",
            "nazwa": "string",
            "teryt7": "string",
            "woj": "string",
            "pow": "string",
            "gmi": "string",
            "rodz_gmi": "string",
            "geom_2180": "string",
        },
    )
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(df.drop(columns=["geom_2180"]), geometry=geom)

    woj = gdf[gdf["typ"] == "województwo"].reset_index(drop=True)
    t2 = time.perf_counter()

    print(f"[WOJ] CSV: {t1 - t0:.6f}s | WKT: {t2 - t1:.6f}s | N={len(woj)}")
    return woj


def load_hex_limited(path, limit):
    print(f"[LOAD] geo_hex ORDER BY hex_0125 LIMIT {limit}")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={"hex_0125": "Int64", "geom_2180": "string"},
    )

    # sortowanie NUMERYCZNE – zgodne z PG
    df = df.sort_values("hex_0125", kind="mergesort").head(limit).reset_index(drop=True)
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(df.drop(columns=["geom_2180"]), geometry=geom)
    t2 = time.perf_counter()

    print(f"[HEX] CSV+SORT+LIMIT: {t1 - t0:.6f}s | WKT: {t2 - t1:.6f}s | N={len(gdf)}")
    return gdf


# =========================================
# EKSPERYMENT 16
# =========================================


def experiment_16_geo_hex_woj_join(woj_gdf, hex_gdf):
    print("\n==================== EKSPERYMENT 16 ====================")
    print("[E16] Spatial join: hex → województwo")
    print("[E16] ST_Intersects + ST_Intersection")
    print("[E16] Indeks przestrzenny: STRtree po stronie województw")

    # -----------------------------------------
    # STRtree (POZA czasem eksperymentu)
    # -----------------------------------------
    t0 = time.perf_counter()
    woj_geoms = list(woj_gdf.geometry.values)
    woj_tree = STRtree(woj_geoms)
    t1 = time.perf_counter()
    print(f"[E16] STRtree(woj) build: {t1 - t0:.6f}s")

    rows = []
    bbox_counts = []

    # -----------------------------------------
    # Właściwe obliczenia
    # -----------------------------------------
    t2 = time.perf_counter()

    for h in hex_gdf.itertuples(index=False):
        hex_id = int(h.hex_0125)
        hex_geom = h.geometry
        area_hex = float(hex_geom.area)

        candidate_idxs = woj_tree.query(hex_geom)
        bbox_counts.append(len(candidate_idxs))

        if candidate_idxs.size == 0:
            continue

        for idx in candidate_idxs:
            w = woj_gdf.iloc[int(idx)]

            if not hex_geom.intersects(w.geometry):
                continue

            inter = hex_geom.intersection(w.geometry)
            if inter.is_empty:
                continue

            rows.append(
                {
                    "hex_id": hex_id,
                    "woj_id": int(w.id),
                    "area_hex_m2": area_hex,
                    "area_intersection_m2": float(inter.area),
                }
            )

    t3 = time.perf_counter()

    print(
        f"[E16] BBox candidates – min: {min(bbox_counts)}, "
        f"max: {max(bbox_counts)}, "
        f"avg: {sum(bbox_counts)/len(bbox_counts):.2f}"
    )
    print(f"[E16] Czas eksperymentu: {t3 - t2:.6f}s")

    # -----------------------------------------
    # Zapis wyników
    # -----------------------------------------
    out = pd.DataFrame(rows)
    out = out.sort_values(["hex_id", "woj_id"])

    out_path = os.path.join(OUT_DIR, "geo_hex_woj_join_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E16] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE DANYCH DO EKSPERYMENTU 16 ===")

    woj = load_woj(PATH_POLSKA)
    hex_sample = load_hex_limited(PATH_HEX, HEX_LIMIT_E16)

    experiment_16_geo_hex_woj_join(woj, hex_sample)

    print("\n=== EKSPERYMENT 16 ZAKOŃCZONY ===")
