import os
import time
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree
from shapely.ops import unary_union

# =========================================
# KONFIGURACJA
# =========================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_HEX = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_hex_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"

# odpowiednik: ORDER BY hex_0125 LIMIT N
HEX_LIMIT_E13 = 1_000_000


# =========================================
# FUNKCJE ŁADOWANIA
# =========================================


def load_geo_polska(path: str) -> gpd.GeoDataFrame:
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
    gdf = gpd.GeoDataFrame(df.drop(columns=["geom_2180"]), geometry=geom).reset_index(drop=True)

    t2 = time.perf_counter()
    print(f"[geo_polska] CSV: {t1 - t0:.3f}s | WKT → geometry: {t2 - t1:.3f}s")
    return gdf


def load_geo_hex_limited(path: str, limit: int) -> gpd.GeoDataFrame:
    print(f"[LOAD] geo_hex ORDER BY hex_0125 LIMIT {limit}")

    t0 = time.perf_counter()
    df = pd.read_csv(
        path,
        dtype={"hex_0125": "Int64", "geom_2180": "string"},
    )

    # SORTOWANIE NUMERYCZNE – równoważne PG
    df = df.sort_values("hex_0125", kind="mergesort").head(limit).reset_index(drop=True)
    t1 = time.perf_counter()

    geom = gpd.GeoSeries.from_wkt(df["geom_2180"], crs=CRS_2180)
    gdf = gpd.GeoDataFrame(df.drop(columns=["geom_2180"]), geometry=geom)

    t2 = time.perf_counter()
    print(f"[geo_hex] CSV+SORT+LIMIT: {t1 - t0:.3f}s | WKT → geometry: {t2 - t1:.3f}s")
    return gdf


# =========================================
# EKSPERYMENT 13
# geo_hex_union_woj
# =========================================


def experiment_13_geo_hex_union_woj(
    geo_polska: gpd.GeoDataFrame,
    geo_hex: gpd.GeoDataFrame,
):
    print("\n==================== EKSPERYMENT 13 ====================")
    print(f"[E13] HEX_LIMIT = {HEX_LIMIT_E13}")
    print("[E13] UnaryUnion heksagonów w obrębie województw")

    # -------------------------------------------------
    # WARSTWA ADMINISTRACYJNA (mała)
    # -------------------------------------------------
    woj = geo_polska[geo_polska["typ"] == "województwo"].reset_index(drop=True)
    print(f"[E13] Województwa: {len(woj)}")

    # -------------------------------------------------
    # INDEKS PRZESTRZENNY (jak GiST na geo_hex)
    # -------------------------------------------------
    hex_geoms = list(geo_hex.geometry.values)

    t_idx0 = time.perf_counter()
    hex_tree = STRtree(hex_geoms)
    t_idx1 = time.perf_counter()
    print(f"[E13] Budowa STRtree (geo_hex): {t_idx1 - t_idx0:.3f} s")

    rows = []

    # -------------------------------------------------
    # CZAS EKSPERYMENTU (bez budowy indeksu)
    # -------------------------------------------------
    t0 = time.perf_counter()

    for w in woj.itertuples(index=False):
        woj_id = int(w.id)
        geom_w = w.geometry

        # 1) PREFILTR BBOX (jak GiST)
        candidate_idxs = hex_tree.query(geom_w)

        if len(candidate_idxs) == 0:
            continue

        # 2) DOKŁADNY ST_Intersects
        intersecting_hexes = [hex_geoms[i] for i in candidate_idxs if hex_geoms[i].intersects(geom_w)]

        if not intersecting_hexes:
            continue

        # 3) ST_UnaryUnion(ST_Collect)
        union_geom = (
            intersecting_hexes[0] if len(intersecting_hexes) == 1 else unary_union(intersecting_hexes)
        )

        rows.append(
            {
                "woj_id": woj_id,
                "geom_union_wkt": union_geom.wkt,
            }
        )

    t1 = time.perf_counter()
    print(f"[E13] Czas obliczeń (bez zapisu): {t1 - t0:.3f} s")

    out = pd.DataFrame(rows)
    out_path = os.path.join(OUT_DIR, "geo_hex_union_woj_py.csv")
    out.to_csv(out_path, index=False)
    print(f"[E13] Zapisano: {out_path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== ŁADOWANIE DANYCH – EKSPERYMENT 13 ===")

    geo_polska = load_geo_polska(PATH_POLSKA)
    geo_hex_limited = load_geo_hex_limited(PATH_HEX, HEX_LIMIT_E13)

    experiment_13_geo_hex_union_woj(geo_polska, geo_hex_limited)

    print("\n=== EKSPERYMENT 13 ZAKOŃCZONY ===")
