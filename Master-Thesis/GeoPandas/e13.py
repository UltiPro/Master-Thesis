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

# Ścieżki – dostosuj do swojego środowiska
PATH_POLSKA = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_polska_2180.csv"
PATH_HEX = r"C:\\Users\\Ultip\\Desktop\\mgr\\pyt\\geo_hex_2180.csv"

OUT_DIR = r"C:\\Users\\Ultip\\Desktop\\mgr\\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# PARAMETR: limit hexagonów jak w SQL (ORDER BY hex_0125 LIMIT N)
# Bez sortowania wczytuje pierwsze N wierszy z pliku
HEX_LIMIT_E13 = 1000000


# =========================================
# FUNKCJE ŁADOWANIA
# =========================================


def load_geo_polska(path: str):
    """Wczytanie geo_polska_2180 z pomiarem czasu."""
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
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180).reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[geo_polska] CSV: {t1 - t0:.6f}s")
    print(f"[geo_polska] WKT → geometry: {t2 - t1:.6f}s")

    return gdf


def load_geo_hex_limited(path: str, hex_limit: int):
    """
    Wczytanie geo_hex z limitem liczby wierszy.
    ZAŁOŻENIE: plik CSV jest już posortowany po hex_0125,
    dzięki czemu nrows=hex_limit odpowiada ORDER BY hex_0125 LIMIT N.
    Jeśli nie – trzeba by wczytać całość i posortować (duży koszt RAM).
    """
    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        nrows=hex_limit,
        dtype={
            "hex_0125": "string",
            "geom_2180": "string",
        },
    )
    t1 = time.perf_counter()

    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180).reset_index(drop=True)

    t2 = time.perf_counter()

    print(f"[geo_hex] CSV (nrows={hex_limit}): {t1 - t0:.6f}s")
    print(f"[geo_hex] WKT → geometry: {t2 - t1:.6f}s")

    return gdf


# =========================================
# EKSPERYMENT 13
# geo_hex_union_woj
# =========================================


def experiment_13_geo_hex_union_woj(geo_polska: gpd.GeoDataFrame, geo_hex_limited: gpd.GeoDataFrame):
    print("\n==================== EKSPERYMENT 13: geo_hex_union_woj ====================")
    print(f"[E13] HEX_LIMIT_E13 = {HEX_LIMIT_E13}")

    # Województwa
    woj = geo_polska[geo_polska["typ"] == "województwo"].copy().reset_index(drop=True)

    # Hexy (ograniczone do HEX_LIMIT_E13)
    hex_gdf = geo_hex_limited.copy().reset_index(drop=True)

    # STRtree dla heksagonów
    hex_geoms = list(hex_gdf.geometry.values)
    hex_tree = STRtree(hex_geoms)
    geom_to_index = {geom: idx for idx, geom in enumerate(hex_geoms)}

    rows = []

    t0 = time.perf_counter()

    # Dla każdego województwa: znajdź przecinające się heksagony → UnaryUnion
    for _, wrow in woj.iterrows():
        woj_id = int(wrow["id"])
        geom_w = wrow.geometry

        # Kandydaci z drzewa przestrzennego
        candidates = hex_tree.query(geom_w)

        if len(candidates) == 0:
            # Brak heksów przecinających województwo
            continue

        idxs = []
        for c in candidates:
            if isinstance(c, (int, np.integer)):
                idxs.append(int(c))
            else:
                idx = geom_to_index.get(c)
                if idx is not None:
                    idxs.append(idx)

        if not idxs:
            continue

        # Zbierz geometrię hexów dla danego województwa
        hex_subset = [hex_geoms[i] for i in idxs]

        # UnaryUnion (odpowiednik ST_UnaryUnion(ST_Collect(...)))
        union_geom = hex_subset[0]
        if len(hex_subset) > 1:
            from shapely.ops import unary_union

            union_geom = unary_union(hex_subset)

        rows.append(
            {
                "woj_id": woj_id,
                "geom_union_wkt": union_geom.wkt,
            }
        )

    t1 = time.perf_counter()
    print(f"[E13] Czas obliczeń (bez zapisu CSV): {t1 - t0:.6f}s")

    # Zapis wyników do CSV
    out = pd.DataFrame(rows)
    out_path = os.path.join(OUT_DIR, "geo_hex_union_woj_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E13] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE danych do eksperymentu 13 ===")

    geo_polska = load_geo_polska(PATH_POLSKA)
    geo_hex_limited = load_geo_hex_limited(PATH_HEX, HEX_LIMIT_E13)

    experiment_13_geo_hex_union_woj(geo_polska, geo_hex_limited)

    print("\n=== EKSPERYMENT 13 ZAKOŃCZONY ===")
