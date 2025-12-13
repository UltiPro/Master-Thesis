import os
import time
import collections

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
import shapely
from shapely.strtree import STRtree
from pyproj import Transformer

# =========================================
# KONFIGURACJA ŚCIEŻEK
# =========================================

PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"
PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"

CRS_2180 = "EPSG:2180"

os.makedirs(OUT_DIR, exist_ok=True)


# =========================================
# POMOCNICZE FUNKCJE
# =========================================


def load_gdf(path, geom_col, crs=CRS_2180, dtype=None):
    """Wczytanie CSV + WKT→geometry z pomiarem czasu."""

    # 1. Wczytanie CSV
    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()
    load_csv_time = t1 - t0
    print(f"[LOAD] CSV {path} → {load_csv_time:.6f} s")

    # 2. Konwersja WKT → Shapely
    t2 = time.perf_counter()
    df["geometry"] = df[geom_col].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=crs)
    t3 = time.perf_counter()
    wkt_time = t3 - t2
    print(f"[LOAD] WKT → geometry ({geom_col}) → {wkt_time:.6f} s")

    # 3. (opcjonalnie) indeks GeoPandas – tylko do raportu czasu
    t4 = time.perf_counter()
    _ = gdf.sindex
    t5 = time.perf_counter()
    sindex_time = t5 - t4
    print(f"[LOAD] GeoPandas sindex → {sindex_time:.6f} s")

    # reset indeksu żeby 0..N-1 zgadzało się z kolejnością geometrii
    gdf = gdf.reset_index(drop=True)

    return gdf, load_csv_time, wkt_time, sindex_time


def safe_id(val):
    """Konwersja ID (Int64 lub Series) do zwykłego int."""
    if isinstance(val, pd.Series):
        return int(val.iloc[0])
    return int(val)


# =========================================
# WCZYTYWANIE DANYCH
# =========================================

print("\n=== Wczytywanie dat_poi_2180 ===")
poi, poi_t_csv, poi_t_wkt, poi_t_idx = load_gdf(
    PATH_POI,
    "geom_point_2180",
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

print("\n=== Wczytywanie geo_polska_2180 ===")
polska, pol_t_csv, pol_t_wkt, pol_t_idx = load_gdf(
    PATH_POLSKA,
    "geom_2180",
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

# STRtree dla wszystkich POI (używany w E1 i E3)
poi_geom = list(poi.geometry.values)
t0 = time.perf_counter()
poi_tree = STRtree(poi_geom)
t1 = time.perf_counter()
print(f"\n[POI] STRtree (Shapely) index → {t1 - t0:.6f} s")

# ===========================
# Punkt referencyjny z 4326 → 2180
# ===========================
lon = 19.46701915338524
lat = 51.74357018348951

transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
x_2180, y_2180 = transformer.transform(lon, lat)

print(f"[REF] Punkt referencyjny 4326: ({lon}, {lat})")
print(f"[REF] Punkt referencyjny 2180: ({x_2180}, {y_2180})")

ref_point = shapely.Point(x_2180, y_2180)

# =========================================
# EKSPERYMENT 1 — Najbliższy POI do punktu
# =========================================

print("\n==================== EKSPERYMENT 1 ====================")

t0 = time.perf_counter()
nearest_geom = poi_tree.nearest(ref_point)

# STRtree może zwrócić geometrię albo indeks – obsługujemy oba przypadki
if isinstance(nearest_geom, (int, np.integer)):
    pos = int(nearest_geom)
else:
    pos = poi_geom.index(nearest_geom)

row_nearest = poi.iloc[pos]
dist_val = float(row_nearest.geometry.distance(ref_point))
t1 = time.perf_counter()

poi_id = safe_id(row_nearest["id"])

print("Najbliższy POI ID:", poi_id)
print("Odległość [m]:", dist_val)
print(f"Czas eksperymentu 1 (Python): {t1 - t0:.6f} s")

df_exp1 = pd.DataFrame(
    [
        {
            "poi_id": poi_id,
            "distance_m": dist_val,
        }
    ]
)
df_exp1.to_csv(os.path.join(OUT_DIR, "feat_poi_nearest_point.csv"), index=False)


# =========================================
# EKSPERYMENT 2 — Najbliższy POI dla każdej kategorii
# =========================================

print("\n==================== EKSPERYMENT 2 ====================")

categories = poi["category"].dropna().unique()
results_exp2 = []

t0_total = time.perf_counter()

for cat in categories:
    subset = poi[poi["category"] == cat].copy()
    if subset.empty:
        continue

    subset = subset.reset_index(drop=True)
    sub_geom = list(subset.geometry.values)
    sub_tree = STRtree(sub_geom)

    nearest_geom = sub_tree.nearest(ref_point)

    if isinstance(nearest_geom, (int, np.integer)):
        pos = int(nearest_geom)
    else:
        pos = sub_geom.index(nearest_geom)

    row_cat = subset.iloc[pos]
    poi_id = safe_id(row_cat["id"])
    dist_val = float(row_cat.geometry.distance(ref_point))

    results_exp2.append(
        {
            "category": cat,
            "poi_id": poi_id,
            "distance_m": dist_val,
        }
    )

t1_total = time.perf_counter()
print(f"Czas eksperymentu 2 (Python): {t1_total - t0_total:.6f} s")

df_exp2 = pd.DataFrame(results_exp2)
df_exp2.to_csv(os.path.join(OUT_DIR, "feat_poi_nearest.csv"), index=False)


# =========================================
# EKSPERYMENT 3 — Liczenie POI w promieniach (ST_DWithin)
# =========================================

print("\n==================== EKSPERYMENT 3 ====================")

radii = [50, 100, 500, 1000, 5000, 50000, 100000]
results_exp3 = []

# używamy tego samego poi_tree i poi_geom
t0_total = time.perf_counter()

# precompute: counts_per_radius[r] = Counter(category → liczba)
counts_per_radius = {}

for r in radii:
    # zapytanie DWithin do STRtree
    res = poi_tree.query(ref_point, predicate="dwithin", distance=r)

    idxs = []
    for item in res:
        if isinstance(item, (int, np.integer)):
            idxs.append(int(item))
        else:
            idxs.append(poi_geom.index(item))

    if len(idxs) == 0:
        counts_per_radius[r] = collections.Counter()
        continue

    cats_r = poi["category"].iloc[idxs]
    counter = collections.Counter([c for c in cats_r if isinstance(c, str)])
    counts_per_radius[r] = counter

# zbuduj listę kategorii z wszystkich promieni
all_cats = set()
for counter in counts_per_radius.values():
    all_cats.update(counter.keys())

for cat in all_cats:
    row = {"category": cat}
    for r in radii:
        cnt = counts_per_radius[r].get(cat, 0)
        row[f"cnt_{r}m"] = int(cnt)
    results_exp3.append(row)

t1_total = time.perf_counter()
print(f"Czas eksperymentu 3 (Python): {t1_total - t0_total:.6f} s")

df_exp3 = pd.DataFrame(results_exp3)
df_exp3.to_csv(os.path.join(OUT_DIR, "feat_poi_multibuffer.csv"), index=False)


# =========================================
# EKSPERYMENT 4 — Odległość do granic jednostek adm.
# =========================================

print("\n==================== EKSPERYMENT 4 ====================")


# Funkcja znajdująca jednostkę administracyjną
def find_unit(point_geom, gdf, sidx, geom_list):
    """
    Wyszukiwanie jednostki administracyjnej (gmina, powiat, woj, kraj)
    odwzorowujące PostGIS ST_Contains + fallback.
    """

    candidates = sidx.query(point_geom)

    if len(candidates) == 0:
        return None

    # zamiana kandydatów na indeksy w gdf (zakładamy reset_index(drop=True))
    real_pos = []
    for c in candidates:
        if isinstance(c, (int, np.integer)):
            real_pos.append(int(c))
        else:
            real_pos.append(geom_list.index(c))

    subset = gdf.iloc[real_pos]

    contains_mask = subset.geometry.contains(point_geom)

    if contains_mask.sum() > 0:
        return subset[contains_mask].iloc[0]

    # fallback: najbliższy polygon
    distances = subset.geometry.distance(point_geom)
    nearest_pos = distances.values.argmin()
    return subset.iloc[nearest_pos]


polska["boundary"] = polska.geometry.boundary

gmina = polska[polska["typ"] == "gmina"].reset_index(drop=True)
powiat = polska[polska["typ"] == "powiat"].reset_index(drop=True)
woj = polska[polska["typ"] == "województwo"].reset_index(drop=True)
kraj = polska[polska["typ"] == "kraj"].reset_index(drop=True)

gmina_geom = list(gmina.geometry.values)
powiat_geom = list(powiat.geometry.values)
woj_geom = list(woj.geometry.values)
kraj_geom = list(kraj.geometry.values)

gmina_tree = STRtree(gmina_geom)
powiat_tree = STRtree(powiat_geom)
woj_tree = STRtree(woj_geom)
kraj_tree = STRtree(kraj_geom)

subset_poi = poi.head(1000)
rows = []

t0 = time.perf_counter()

for _, p in subset_poi.iterrows():
    geom_p = p.geometry

    gmi_row = find_unit(geom_p, gmina, gmina_tree, gmina_geom)
    pow_row = find_unit(geom_p, powiat, powiat_tree, powiat_geom)
    woj_row = find_unit(geom_p, woj, woj_tree, woj_geom)
    kraj_row = find_unit(geom_p, kraj, kraj_tree, kraj_geom)

    rows.append(
        {
            "poi_id": safe_id(p["id"]),
            "dist_gmina": float(geom_p.distance(gmi_row["boundary"])),
            "dist_powiat": float(geom_p.distance(pow_row["boundary"])),
            "dist_woj": float(geom_p.distance(woj_row["boundary"])),
            "dist_kraj": float(geom_p.distance(kraj_row["boundary"])),
        }
    )

t1 = time.perf_counter()
print(f"Czas eksperymentu 4 (Python): {t1 - t0:.6f} s")

df_exp4 = pd.DataFrame(rows)
df_exp4.to_csv(os.path.join(OUT_DIR, "feat_poi_border.csv"), index=False)

print("\n==================== PODSUMOWANIE PRZYGOTOWANIA DANYCH ====================")
print(f"[POI]    CSV: {poi_t_csv:.6f}s | WKT: {poi_t_wkt:.6f}s | sindex(GeoPandas): {poi_t_idx:.6f}s")
print(f"[POLSKA] CSV: {pol_t_csv:.6f}s | WKT: {pol_t_wkt:.6f}s | sindex(GeoPandas): {pol_t_idx:.6f}s")
print("===========================================================================")
