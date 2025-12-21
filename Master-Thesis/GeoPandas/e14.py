import os
import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree

# =========================================
# KONFIGURACJA
# =========================================

PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"
PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# =========================================
# WCZYTYWANIE DANYCH
# =========================================


def load_hex(path: str) -> gpd.GeoDataFrame:
    print("[LOAD] HEX (FULL DATASET)")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={
            "hex_0125": "Int64",
            "geom_2180": "string",
        },
    )
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(
        df.drop(columns=["geom_2180"]),
        geometry=geom,
    ).reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[HEX] CSV={t1 - t0:.4f}s | WKT={t2 - t1:.4f}s | N={len(gdf)}")
    return gdf


def load_poi(path: str) -> gpd.GeoDataFrame:
    print("[LOAD] POI")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={
            "id": "Int64",
            "geom_point_2180": "string",
        },
    )
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_point_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(
        df.drop(columns=["geom_point_2180"]),
        geometry=geom,
    ).reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[POI] CSV={t1 - t0:.4f}s | WKT={t2 - t1:.4f}s | N={len(gdf)}")
    return gdf


# =========================================
# EKSPERYMENT 14
# =========================================


def experiment_14_hex_poi_counts(hex_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame):
    """
    Odpowiednik SQL (PostGIS):

    SELECT h.hex_0125, COUNT(p.id)
    FROM geo_hex h
    LEFT JOIN dat_poi p
      ON ST_Contains(h.geom, p.geom)
    GROUP BY h.hex_0125;
    """

    print("\n==================== EKSPERYMENT 14 ====================")
    print(f"[E14] HEX={len(hex_gdf)} | POI={len(poi_gdf)}")
    print("[E14] ST_Contains(hex, poi) – pełny zbiór danych")

    # -----------------------------------------------------
    # Budowa indeksu STRtree (POI = zbiór przeszukiwany)
    # -----------------------------------------------------
    t0 = time.perf_counter()

    poi_geoms = list(poi_gdf.geometry.values)
    poi_tree = STRtree(poi_geoms)

    t1 = time.perf_counter()
    print(f"[E14] STRtree (POI) build: {t1 - t0:.4f}s")

    results = []

    # -----------------------------------------------------
    # Właściwy eksperyment
    # -----------------------------------------------------
    t2 = time.perf_counter()

    for h in hex_gdf.itertuples(index=False):
        hex_geom = h.geometry

        # 1) PREFILTR BBOX (jak GiST)
        candidate_idxs = poi_tree.query(hex_geom)

        if candidate_idxs.size == 0:
            results.append(
                {
                    "hex_0125": int(h.hex_0125),
                    "poi_count": 0,
                }
            )
            continue

        # 2) DOKŁADNY PREDYKAT – ST_Contains
        count = 0
        for idx in candidate_idxs:
            if poi_geoms[idx].within(hex_geom):
                count += 1

        results.append(
            {
                "hex_0125": int(h.hex_0125),
                "poi_count": count,
            }
        )

    t3 = time.perf_counter()
    print(f"[E14] Czas obliczeń: {t3 - t2:.4f}s")

    # -----------------------------------------------------
    # Zapis wyników
    # -----------------------------------------------------
    out = pd.DataFrame(results)
    out_path = os.path.join(OUT_DIR, "hex_poi_counts_py.csv")
    out.to_csv(out_path, index=False)

    print(f"[E14] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE DANYCH – EKSPERYMENT 14 ===")

    hex_gdf = load_hex(PATH_HEX)
    poi_gdf = load_poi(PATH_POI)

    experiment_14_hex_poi_counts(hex_gdf, poi_gdf)

    print("\n=== EKSPERYMENT 14 ZAKOŃCZONY ===")
