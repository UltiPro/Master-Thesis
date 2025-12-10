import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.strtree import STRtree

# =========================================
# KONFIGURACJA
# =========================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# Domyślny limit hexów (jak w SQL było 1000)
HEX_LIMIT_E16 = 1000  # możesz zmieniać (1000, 10000, 50000, ...)


# =========================================
# WCZYTYWANIE DANYCH
# =========================================


def load_woj(path):
    print("[LOAD] geo_polska (województwa)")

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

    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)

    # filtrujemy tylko województwa
    woj = gdf[gdf["typ"] == "województwo"].copy().reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[WOJ] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(woj)}")
    return woj


def load_hex_limited(path, limit):
    print(f"[LOAD] geo_hex (limit={limit})")

    t0 = time.perf_counter()
    # zakładamy, że plik jest już posortowany po hex_0125
    df = pd.read_csv(
        path,
        dtype={
            "hex_0125": "Int64",
            "geom_2180": "string",
        },
        nrows=limit,
    )
    t1 = time.perf_counter()

    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180)

    # dodatkowo sortujemy po hex_0125 dla zgodności z:
    # ORDER BY hex_0125 LIMIT N
    gdf = gdf.sort_values("hex_0125").reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[HEX] CSV={t1 - t0:.4f}s  WKT={t2 - t1:.4f}s  count={len(gdf)}")
    return gdf


# =========================================
# EKSPERYMENT 16 – geo_hex_woj_join
# =========================================


def experiment_16_geo_hex_woj_join(woj_gdf, hex_gdf):
    """
    Odpowiednik SQL:

    WITH woj AS (
        SELECT id AS woj_id, nazwa AS woj_name, geom_2180
        FROM geo_polska
        WHERE typ = 'województwo'
    ),
    hex_sample AS (
        SELECT hex_0125 AS hex_id, geom_2180
        FROM geo_hex
        ORDER BY hex_0125
        LIMIT 1000
    )
    SELECT
        h.hex_id,
        w.woj_id,
        ST_Area(h.geom_2180) AS area_hex_m2,
        ST_Area(ST_Intersection(h.geom_2180, w.geom_2180)) AS area_intersection_m2
    FROM hex_sample h
    JOIN woj w
        ON ST_Intersects(h.geom_2180, w.geom_2180)
    WHERE ST_Intersection(h.geom_2180, w.geom_2180) IS NOT NULL;
    """

    print("\n==================== EKSPERYMENT 16 – geo_hex_woj_join ====================")

    # -----------------------------------------
    # STRtree po województwach
    # -----------------------------------------
    t0 = time.perf_counter()
    woj_geoms = list(woj_gdf.geometry.values)
    tree = STRtree(woj_geoms)
    geom_to_index = {geom: idx for idx, geom in enumerate(woj_geoms)}
    t1 = time.perf_counter()

    print(f"[E16] STRtree(woj): {t1 - t0:.4f}s")

    rows = []

    # -----------------------------------------
    # Pętla po hexach
    # -----------------------------------------
    t2 = time.perf_counter()

    for _, h in hex_gdf.iterrows():
        hex_id = int(h["hex_0125"])
        hex_geom = h.geometry

        # ST_Area(h.geom_2180)
        area_hex = float(hex_geom.area)

        # kandydaci województw przez STRtree (bbox)
        candidates = tree.query(hex_geom)

        if len(candidates) == 0:
            # brak przecięć → w SQL w ogóle nie ma rekordu, więc też pomijamy
            continue

        candidate_positions = []
        for c in candidates:
            if isinstance(c, (int, np.integer)):
                candidate_positions.append(int(c))
            else:
                idx = geom_to_index.get(c, None)
                if idx is not None:
                    candidate_positions.append(idx)

        if not candidate_positions:
            continue

        woj_subset = woj_gdf.iloc[candidate_positions]

        # dokładny ST_Intersects + ST_Intersection
        for _, w in woj_subset.iterrows():
            geom_w = w.geometry

            if not hex_geom.intersects(geom_w):
                continue

            inter = hex_geom.intersection(geom_w)
            if inter.is_empty:
                continue

            area_inter = float(inter.area)

            rows.append(
                {
                    "hex_id": hex_id,
                    "woj_id": int(w["id"]),
                    "area_hex_m2": area_hex,
                    "area_intersection_m2": area_inter,
                }
            )

    t3 = time.perf_counter()
    print(f"[E16] Czas obliczeń: {t3 - t2:.4f}s")

    # -----------------------------------------
    # Zapis wyników
    # -----------------------------------------
    if rows:
        out = pd.DataFrame(rows).sort_values(["hex_id", "woj_id"])
    else:
        out = pd.DataFrame(columns=["hex_id", "woj_id", "area_hex_m2", "area_intersection_m2"])

    out_path = os.path.join(OUT_DIR, "geo_hex_woj_join_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E16] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE DANYCH DO E16 ===")
    woj = load_woj(PATH_POLSKA)
    hex_sample = load_hex_limited(PATH_HEX, HEX_LIMIT_E16)

    experiment_16_geo_hex_woj_join(woj, hex_sample)

    print("\n=== EKSPERYMENT 16 ZAKOŃCZONY ===")
