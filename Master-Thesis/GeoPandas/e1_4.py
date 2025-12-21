import os
import time

import pandas as pd
import numpy as np
import geopandas as gpd
import shapely
from pyproj import Transformer
from shapely.strtree import STRtree

# =========================================
# KONFIGURACJA ŚCIEŻEK
# =========================================

PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"
PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
CRS_2180 = "EPSG:2180"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================================
# FUNKCJE POMOCNICZE
# =========================================


def load_gdf(path, geom_col, crs=CRS_2180, dtype=None):
    """
    CSV + WKT → GeoDataFrame
    Czas wczytywania, WKT i budowy sindex raportowany osobno
    """

    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()
    load_csv_time = t1 - t0
    print(f"[LOAD] CSV {path} → {load_csv_time:.6f} s")

    t2 = time.perf_counter()
    geom = gpd.GeoSeries.from_wkt(df[geom_col], crs=crs)
    gdf = gpd.GeoDataFrame(df.drop(columns=[geom_col]), geometry=geom)
    t3 = time.perf_counter()
    wkt_time = t3 - t2
    print(f"[LOAD] WKT → geometry ({geom_col}) → {wkt_time:.6f} s")

    gdf = gdf.reset_index(drop=True)

    t4 = time.perf_counter()
    sidx = gdf.sindex
    t5 = time.perf_counter()
    sindex_time = t5 - t4
    print(f"[LOAD] GeoPandas sindex build → {sindex_time:.6f} s")

    return gdf, sidx, load_csv_time, wkt_time, sindex_time


def safe_id(val):
    if isinstance(val, pd.Series):
        return int(val.iloc[0])
    return int(val)


def nearest_point_by_sindex(gdf, sidx, ref_point, start_side=50.0, grow=2.0, max_side=200000.0):
    side = float(start_side)

    while True:
        bbox = (
            ref_point.x - side,
            ref_point.y - side,
            ref_point.x + side,
            ref_point.y + side,
        )

        idx = list(sidx.intersection(bbox))
        candidates = gdf.iloc[idx]

        if len(candidates) > 0:
            dists = candidates.geometry.distance(ref_point)
            pos = dists.idxmin()
            return gdf.loc[pos], len(candidates), side

        side *= grow
        if side > max_side:
            raise RuntimeError("Nie znaleziono kandydatów – sprawdź CRS/dane.")


def nearest_in_category(gdf, sidx, ref_point, cat, start_side=200.0, grow=2.0, max_side=200000.0):
    side = float(start_side)

    while True:
        bbox = (
            ref_point.x - side,
            ref_point.y - side,
            ref_point.x + side,
            ref_point.y + side,
        )

        idx = list(sidx.intersection(bbox))
        candidates = gdf.iloc[idx]
        cand_cat = candidates[candidates["category"] == cat]

        if len(cand_cat) > 0:
            dists = cand_cat.geometry.distance(ref_point)
            pos = dists.idxmin()
            return gdf.loc[pos], len(candidates), len(cand_cat), side

        side *= grow
        if side > max_side:
            return None, len(candidates), 0, side


def find_unit_gpd(point_geom, gdf_sub, sidx_sub):
    idx = list(sidx_sub.intersection(point_geom.bounds))
    if not idx:
        return None, 0

    candidates = gdf_sub.iloc[idx]
    mask = candidates.geometry.contains(point_geom)

    if mask.any():
        return candidates[mask].iloc[0], len(candidates)

    dists = candidates.geometry.distance(point_geom)
    pos = dists.idxmin()
    return gdf_sub.loc[pos], len(candidates)


# =========================================
# WCZYTYWANIE DANYCH
# =========================================

print("\n=== Wczytywanie dat_poi_2180 ===")
poi, poi_sidx, poi_t_csv, poi_t_wkt, poi_t_idx = load_gdf(
    PATH_POI,
    "geom_point_2180",
    dtype={"id": "Int64", "category": "string", "geom_point_2180": "string"},
)

print("\n=== Wczytywanie geo_polska_2180 ===")
polska, polska_sidx, pol_t_csv, pol_t_wkt, pol_t_idx = load_gdf(
    PATH_POLSKA,
    "geom_2180",
    dtype={"id": "Int64", "typ": "string", "geom_2180": "string"},
)

poi["category"] = poi["category"].astype("category")
polska["typ"] = polska["typ"].astype("category")

# =========================================
# Punkt referencyjny
# =========================================

transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
x, y = transformer.transform(19.46701915338524, 51.74357018348951)

print(f"\n[REF] Punkt referencyjny 4326: (19.46701915338524, 51.74357018348951)")
print(f"[REF] Punkt referencyjny 2180: ({x}, {y})")

ref_point = shapely.Point(x, y)

# =========================================
# EKSPERYMENT 1
# =========================================

print("\n==================== EKSPERYMENT 1b (STRtree NN) ====================")

poi_geoms = list(poi.geometry.values)
tree = STRtree(poi_geoms)

t0 = time.perf_counter()

nearest = tree.nearest(ref_point)

# mapowanie geometria → index
if isinstance(nearest, (int, np.integer)):
    idx = int(nearest)
else:
    idx = poi_geoms.index(nearest)

row = poi.iloc[idx]
dist_val = float(row.geometry.distance(ref_point))

t1 = time.perf_counter()

print(f"Czas eksperymentu 1b (STRtree): {t1 - t0:.6f} s")


# =========================================
# EKSPERYMENT 2
# =========================================

print("\n==================== EKSPERYMENT 2 (GeoPandas sindex) ====================")

categories = poi["category"].dropna().unique()
rows = []

t0 = time.perf_counter()

for cat in categories:
    row, n_bbox, n_cat, side = nearest_in_category(poi, poi_sidx, ref_point, cat)
    if row is None:
        continue

    rows.append(
        {
            "category": str(cat),
            "poi_id": safe_id(row["id"]),
            "distance_m": float(row.geometry.distance(ref_point)),
            "n_bbox_candidates": int(n_bbox),
            "n_cat_candidates": int(n_cat),
            "bbox_side": float(side),
        }
    )

t1 = time.perf_counter()
print(f"Czas eksperymentu 2: {t1 - t0:.6f} s")

# --- zapis POZA pomiarem ---
pd.DataFrame(rows).to_csv(
    os.path.join(OUT_DIR, "exp2_poi_nearest_by_category_py.csv"),
    index=False,
)


# =========================================
# EKSPERYMENT 3 — Liczba POI per kategoria w promieniach
# =========================================

print("\n==================== EKSPERYMENT 3 (GeoPandas sindex) ====================")
print("[E3] Liczba POI z każdej kategorii w promieniach od punktu referencyjnego")

radii = [50, 100, 500, 1000, 5000, 50000, 100000]

t0 = time.perf_counter()

# przechowamy wyniki jako: radius -> Series(category -> count)
counts_by_radius = {}
stats_rows = []  # do logów/metadanych (bbox, within)

for r in radii:
    buf = ref_point.buffer(r)

    # prefiltr bbox przez indeks przestrzenny
    idx = list(poi_sidx.intersection(buf.bounds))
    candidates = poi.iloc[idx]

    if len(candidates) == 0:
        # brak kandydatów = same zera
        counts_by_radius[r] = pd.Series(dtype="int64")
        stats_rows.append(
            {
                "radius_m": r,
                "n_total_poi": len(poi),
                "n_bbox_candidates": 0,
                "n_within_radius": 0,
            }
        )
        print(f"r={r:>6}m | N total={len(poi)} | N bbox candidates=0 | N within=0")
        continue

    # dokładna predykcja: dystans metryczny w EPSG:2180
    dists = candidates.geometry.distance(ref_point)
    within = candidates[dists <= r]

    # policz per kategoria (tylko w obrębie within)
    # observed=True -> bez generowania nieobecnych kategorii
    cat_counts = within.groupby("category", observed=True).size()
    counts_by_radius[r] = cat_counts

    stats_rows.append(
        {
            "radius_m": r,
            "n_total_poi": len(poi),
            "n_bbox_candidates": int(len(candidates)),
            "n_within_radius": int(len(within)),
        }
    )

    print(
        f"r={r:>6}m | N total={len(poi)} | "
        f"N bbox candidates={len(candidates)} | N within={len(within)}"
    )

t1 = time.perf_counter()
print(f"Czas eksperymentu 3: {t1 - t0:.6f} s")

# 1) Wynik główny: tabela (category × promień)
# zbuduj pełną listę kategorii występujących w jakimkolwiek promieniu
all_categories = set()
for s in counts_by_radius.values():
    all_categories.update([c for c in s.index if pd.notna(c)])

rows_out = []
for cat in sorted(all_categories, key=lambda x: str(x)):
    row = {"category": str(cat)}
    for r in radii:
        row[f"cnt_{r}m"] = int(counts_by_radius[r].get(cat, 0))
    rows_out.append(row)

df_exp3 = pd.DataFrame(rows_out)
df_exp3.to_csv(
    os.path.join(OUT_DIR, "exp3_poi_counts_per_category_by_radius_py.csv"),
    index=False,
)


# =========================================
# EKSPERYMENT 4
# =========================================

print("\n==================== EKSPERYMENT 4 (GeoPandas sindex) ====================")

polska["boundary"] = polska.geometry.boundary
layers = {}

for typ in ["gmina", "powiat", "województwo", "kraj"]:
    sub = polska[polska["typ"] == typ].reset_index(drop=True)
    layers[typ] = (sub, sub.sindex)

rows = []
subset_poi = poi.head(500000)

t0 = time.perf_counter()

for p in subset_poi.itertuples(index=False):
    row = {"poi_id": int(p.id)}

    for typ, (gdf_sub, sidx_sub) in layers.items():
        unit, n_bbox = find_unit_gpd(p.geometry, gdf_sub, sidx_sub)
        row[f"n_bbox_{typ}"] = int(n_bbox)
        row[f"dist_{typ}"] = float(p.geometry.distance(unit["boundary"])) if unit is not None else None

    rows.append(row)

t1 = time.perf_counter()
print(f"Czas eksperymentu 4: {t1 - t0:.6f} s")

# --- zapis POZA pomiarem ---
pd.DataFrame(rows).to_csv(
    os.path.join(OUT_DIR, "exp4_poi_distance_to_admin_py.csv"),
    index=False,
)


# =========================================
# PODSUMOWANIE
# =========================================

print("\n==================== PODSUMOWANIE PRZYGOTOWANIA DANYCH ====================")
print(f"[POI]    CSV: {poi_t_csv:.6f}s | WKT: {poi_t_wkt:.6f}s | sindex: {poi_t_idx:.6f}s | N={len(poi)}")
print(
    f"[POLSKA] CSV: {pol_t_csv:.6f}s | WKT: {pol_t_wkt:.6f}s | sindex: {pol_t_idx:.6f}s | N={len(polska)}"
)
print("============================================================================")
