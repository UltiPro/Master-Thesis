import os
import time

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
import shapely
from shapely.strtree import STRtree
from shapely.ops import voronoi_diagram

# =========================================
# KONFIGURACJA ŚCIEŻEK
# =========================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
os.makedirs(OUT_DIR, exist_ok=True)

CRS_2180 = "EPSG:2180"


# =========================================
# FUNKCJA NAPRAWCZA STRtree → INDEX
# =========================================


def normalize_strtree_result(item, geom_list, geom_to_index):
    """
    Normalizuje wynik STRtree:
      - jeśli zwrócono integer (np.int64) → to już index
      - jeśli zwrócono geometrię → szukamy jej indeksu
    """

    if isinstance(item, (int, np.integer)):
        return int(item)

    idx = geom_to_index.get(item)
    if idx is not None:
        return idx

    # fallback (wolniejszy, ale 100% pewny)
    return geom_list.index(item)


# =========================================
# WCZYTYWANIE DANYCH
# =========================================


def load_geo_polska():
    t0 = time.perf_counter()
    df = pd.read_csv(
        PATH_POLSKA,
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
    print(f"[geo_polska] Wczytanie CSV: {t1 - t0:.6f} s")

    t2 = time.perf_counter()
    df["geometry"] = df["geom_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180).reset_index(drop=True)
    t3 = time.perf_counter()
    print(f"[geo_polska] WKT → geometry: {t3 - t2:.6f} s")

    return gdf


def load_dat_poi():
    t0 = time.perf_counter()
    df = pd.read_csv(
        PATH_POI,
        dtype={
            "id": "Int64",
            "osm_id": "Int64",
            "name_brand": "string",
            "name_brand_clean": "string",
            "name": "string",
            "name_clean": "string",
            "source_name": "string",
            "category": "string",
            "geom_point_2180": "string",
        },
    )
    t1 = time.perf_counter()
    print(f"[dat_poi] Wczytanie CSV: {t1 - t0:.6f} s")

    t2 = time.perf_counter()
    df["geometry"] = df["geom_point_2180"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_2180).reset_index(drop=True)
    t3 = time.perf_counter()
    print(f"[dat_poi] WKT → geometry: {t3 - t2:.6f} s")

    return gdf


# =========================================
# EKSPERYMENT 5
# =========================================


def experiment_5_geo_polska_geom_features(geo_polska):
    print("\n==================== EKSPERYMENT 5 ====================")
    global_start = time.perf_counter()

    area_m2 = geo_polska.geometry.area
    perimeter_m = geo_polska.geometry.length
    centroid = geo_polska.geometry.centroid

    global_end = time.perf_counter()
    print(f"[E5] Czas całkowity: {global_end - global_start:.6f} s")

    out = pd.DataFrame(
        {
            "id": geo_polska["id"],
            "nazwa": geo_polska["nazwa"],
            "typ": geo_polska["typ"],
            "area_m2": area_m2,
            "perimeter_m": perimeter_m,
            "centroid_2180": centroid.to_wkt(),
        }
    )

    path = os.path.join(OUT_DIR, "geo_polska_geom_features_py.csv")
    out.to_csv(path, index=False)
    print(f"[E5] Zapisano: {path}")


# =========================================
# EKSPERYMENT 6
# =========================================


def experiment_6_geo_polska_buffer_intersection(geo_polska):
    print("\n==================== EKSPERYMENT 6 ====================")
    total_start = time.perf_counter()

    woj = geo_polska[geo_polska["typ"] == "województwo"].reset_index(drop=True)
    gminy = geo_polska[geo_polska["typ"] == "gmina"].reset_index(drop=True)

    woj_geoms = list(woj.geometry.values)
    woj_tree = STRtree(woj_geoms)
    geom_to_index = {geom: i for i, geom in enumerate(woj_geoms)}

    # BUFFER
    gminy["geom_buffer_5km"] = gminy.geometry.buffer(5000, resolution=8)

    rows = []

    # INTERSECTION
    for _, g in gminy.iterrows():
        buf = g["geom_buffer_5km"]

        candidates = woj_tree.query(buf)
        if len(candidates) == 0:
            continue

        positions = [normalize_strtree_result(c, woj_geoms, geom_to_index) for c in candidates]

        for pos in positions:
            geom_w = woj.geometry.iloc[pos]

            if not buf.intersects(geom_w):
                continue

            inter = buf.intersection(geom_w)
            if inter.is_empty:
                continue

            rows.append(
                {
                    "gmina_id": int(g["id"]),
                    "woj_id": int(woj["id"].iloc[pos]),
                    "area_intersection_m2": float(inter.area),
                    "geom_intersection_wkt": inter.wkt,
                }
            )

    total_end = time.perf_counter()
    print(f"[E6] Czas całkowity: {total_end - total_start:.6f} s")

    out = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "geo_polska_buffer_intersection_py.csv")
    out.to_csv(path, index=False)
    print(f"[E6] Zapisano: {path}")


# =========================================
# EKSPERYMENT 8
# =========================================


def experiment_8_voronoi_limited(geo_polska, poi):
    print("\n==================== EKSPERYMENT 8 ====================")
    total_start = time.perf_counter()

    # 1. 1000 punktów
    pts = poi.head(1000)
    point_geoms = list(pts.geometry.values)

    # 2. Envelope
    envelope = shapely.MultiPoint(point_geoms).envelope

    # 3. Voronoi
    vor_gc = voronoi_diagram(
        shapely.MultiPoint(point_geoms), envelope=envelope, tolerance=0.0, edges=False
    )

    if hasattr(vor_gc, "geoms"):
        vor_cells = [g for g in vor_gc.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
    else:
        vor_cells = [vor_gc]

    vor_list = vor_cells
    vor_to_index = {geom: i for i, geom in enumerate(vor_list)}

    woj = geo_polska[geo_polska["typ"] == "województwo"].reset_index(drop=True)

    vor_tree = STRtree(vor_list)

    rows = []

    for _, w in woj.iterrows():
        geom_w = w.geometry

        candidates = vor_tree.query(geom_w)
        if len(candidates) == 0:
            continue

        positions = [normalize_strtree_result(c, vor_list, vor_to_index) for c in candidates]

        for pos in positions:
            cell = vor_list[pos]

            if not cell.intersects(geom_w):
                continue

            inter = cell.intersection(geom_w)
            if inter.is_empty:
                continue

            rows.append(
                {
                    "woj_id": int(w["id"]),
                    "woj_name": w["nazwa"],
                    "area_intersection_m2": float(inter.area),
                }
            )

    total_end = time.perf_counter()
    print(f"[E8] Czas całkowity: {total_end - total_start:.6f} s")

    df = pd.DataFrame(rows)
    if df.empty:
        out = pd.DataFrame(columns=["woj_id", "woj_name", "voronoi_cell_count", "area_sum_m2"])
    else:
        out = (
            df.groupby(["woj_id", "woj_name"])
            .agg(
                voronoi_cell_count=("area_intersection_m2", "count"),
                area_sum_m2=("area_intersection_m2", "sum"),
            )
            .reset_index()
        )

    path = os.path.join(OUT_DIR, "voronoi_limited_py.csv")
    out.to_csv(path, index=False)
    print(f"[E8] Zapisano: {path}")


# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    print("=== Ładowanie danych źródłowych (geo_polska, dat_poi) ===")
    geo_polska = load_geo_polska()
    poi = load_dat_poi()

    experiment_5_geo_polska_geom_features(geo_polska)
    experiment_6_geo_polska_buffer_intersection(geo_polska)
    experiment_8_voronoi_limited(geo_polska, poi)

    print("\nWszystkie eksperymenty 5–8 wykonane poprawnie.")
