import os
import time
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import voronoi_diagram

# =====================================================
# KONFIGURACJA
# =====================================================

PATH_POLSKA = r"C:\Users\Ultip\Desktop\mgr\pyt\geo_polska_2180.csv"
PATH_POI = r"C:\Users\Ultip\Desktop\mgr\pyt\dat_poi_2180.csv"

OUT_DIR = r"C:\Users\Ultip\Desktop\mgr\experiments"
CRS = "EPSG:2180"

os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================
# ŁADOWANIE DANYCH (BEZ sindex)
# =====================================================


def load_gdf(path, geom_col, dtype):
    t0 = time.perf_counter()
    df = pd.read_csv(path, dtype=dtype)
    t1 = time.perf_counter()
    print(f"[LOAD] CSV {os.path.basename(path)}: {t1 - t0:.6f} s")

    t2 = time.perf_counter()
    geom = gpd.GeoSeries.from_wkt(df[geom_col], crs=CRS)
    gdf = gpd.GeoDataFrame(df.drop(columns=[geom_col]), geometry=geom)
    t3 = time.perf_counter()
    print(f"[LOAD] WKT → geometry: {t3 - t2:.6f} s")

    return gdf.reset_index(drop=True)


# =====================================================
# EKSPERYMENT 5
# =====================================================


def experiment_5_geom_features(geo_polska):
    print("\n==================== EKSPERYMENT 5 ====================")
    print("[E5] Operacje lokalne – brak indeksów przestrzennych")
    print(f"[E5] Liczba jednostek: {len(geo_polska)}")

    t0 = time.perf_counter()

    out = pd.DataFrame(
        {
            "id": geo_polska["id"],
            "nazwa": geo_polska["nazwa"],
            "typ": geo_polska["typ"],
            "area_m2": geo_polska.geometry.area,
            "perimeter_m": geo_polska.geometry.length,
            "centroid_wkt": geo_polska.geometry.centroid.to_wkt(),
        }
    )

    t1 = time.perf_counter()
    print(f"[E5] Czas eksperymentu: {t1 - t0:.6f} s")

    out.to_csv(
        os.path.join(OUT_DIR, "geo_polska_geom_features_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 6
# =====================================================


def experiment_6_buffer_intersection(geo_polska):
    print("\n==================== EKSPERYMENT 6 ====================")
    print("[E6] Bufor gmin (5 km) ∩ województwa")
    print("[E6] Indeks przestrzenny po stronie województw")

    gmina = geo_polska[geo_polska["typ"] == "gmina"].reset_index(drop=True)
    woj = geo_polska[geo_polska["typ"] == "województwo"].reset_index(drop=True)

    print(f"[E6] Gminy: {len(gmina)} | Województwa: {len(woj)}")

    gmina["buffer_5km"] = gmina.geometry.buffer(5000, resolution=8)
    woj_sidx = woj.sindex

    bbox_counts = []
    rows = []

    t0 = time.perf_counter()

    for g in gmina.itertuples(index=False):
        buf = g.buffer_5km
        idx = list(woj_sidx.intersection(buf.bounds))
        bbox_counts.append(len(idx))

        for w in woj.iloc[idx].itertuples(index=False):
            if not buf.intersects(w.geometry):
                continue
            inter = buf.intersection(w.geometry)
            if not inter.is_empty:
                rows.append(
                    {
                        "gmina_id": int(g.id),
                        "woj_id": int(w.id),
                        "area_intersection_m2": float(inter.area),
                    }
                )

    t1 = time.perf_counter()

    print(
        f"[E6] BBox candidates – min: {min(bbox_counts)}, "
        f"max: {max(bbox_counts)}, "
        f"avg: {sum(bbox_counts)/len(bbox_counts):.2f}"
    )
    print(f"[E6] Czas eksperymentu: {t1 - t0:.6f} s")

    pd.DataFrame(rows).to_csv(
        os.path.join(OUT_DIR, "geo_polska_buffer_intersection_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 7 (PEŁNY CZAS)
# =====================================================


def experiment_7_sjoin(poi, geo_polska):
    print("\n==================== EKSPERYMENT 7 ====================")
    print("[E7] Spatial join POI → jednostki administracyjne (4 poziomy)")
    print("[E7] Jeden łączny czas eksperymentu")

    levels = ["kraj", "województwo", "powiat", "gmina"]
    admin_all = geo_polska[geo_polska["typ"].isin(levels)].reset_index(drop=True)

    # preprocessing (poza czasem eksperymentu)
    _ = poi.sindex
    _ = admin_all.sindex

    results = []

    t0_global = time.perf_counter()

    for level in levels:
        admin_lvl = admin_all[admin_all["typ"] == level].reset_index(drop=True)

        print(f"[E7] {level}: POI={len(poi)} | jednostek={len(admin_lvl)}")

        joined = gpd.sjoin(
            poi[["id", "geometry"]],
            admin_lvl[["id", "nazwa", "typ", "geometry"]],
            how="inner",
            predicate="within",
        )

        print(f"[E7] {level}: relacji POI→admin = {len(joined)}")

        out = (
            joined.groupby(["id_right", "nazwa", "typ"], observed=True)
            .size()
            .reset_index(name="poi_count")
            .rename(columns={"id_right": "admin_id"})
        )

        out["level"] = level
        results.append(out)

    t1_global = time.perf_counter()
    print(f"[E7] Czas EKSPERYMENTU 7 (łącznie): {t1_global - t0_global:.6f} s")

    pd.concat(results).to_csv(
        os.path.join(OUT_DIR, "feat_poi_per_admin_4levels_sjoin_py.csv"),
        index=False,
    )


# =====================================================
# EKSPERYMENT 8
# =====================================================


def experiment_8_voronoi(geo_polska, poi):
    print("\n==================== EKSPERYMENT 8 ====================")
    print("[E8] Voronoi (1000 POI) ∩ województwa")

    pts = poi.head(1000)
    points = shapely.MultiPoint(list(pts.geometry.values))
    envelope = points.envelope

    t0 = time.perf_counter()
    vor = voronoi_diagram(points, envelope=envelope, edges=False)
    t1 = time.perf_counter()
    print(f"[E8] Voronoi build time: {t1 - t0:.6f} s")

    vor_cells = list(vor.geoms)
    vor_gdf = gpd.GeoDataFrame(
        {"cell_id": range(len(vor_cells))},
        geometry=vor_cells,
        crs=CRS,
    )

    print(f"[E8] Liczba komórek Voronoi: {len(vor_gdf)}")

    vor_sidx = vor_gdf.sindex
    woj = geo_polska[geo_polska["typ"] == "województwo"].reset_index(drop=True)

    bbox_counts = []
    rows = []

    t2 = time.perf_counter()

    for w in woj.itertuples(index=False):
        idx = list(vor_sidx.intersection(w.geometry.bounds))
        bbox_counts.append(len(idx))

        for c in vor_gdf.iloc[idx].itertuples(index=False):
            if c.geometry.intersects(w.geometry):
                inter = c.geometry.intersection(w.geometry)
                if not inter.is_empty:
                    rows.append(
                        {
                            "woj_id": int(w.id),
                            "woj_name": w.nazwa,
                            "area_intersection_m2": float(inter.area),
                        }
                    )

    t3 = time.perf_counter()

    print(
        f"[E8] BBox candidates – min: {min(bbox_counts)}, "
        f"max: {max(bbox_counts)}, "
        f"avg: {sum(bbox_counts)/len(bbox_counts):.2f}"
    )
    print(f"[E8] Czas eksperymentu: {t3 - t2:.6f} s")

    pd.DataFrame(rows).groupby(["woj_id", "woj_name"]).agg(
        voronoi_cell_count=("area_intersection_m2", "count"),
        area_sum_m2=("area_intersection_m2", "sum"),
    ).reset_index().to_csv(
        os.path.join(OUT_DIR, "voronoi_limited_py.csv"),
        index=False,
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("=== Ładowanie danych ===")

    geo_polska = load_gdf(
        PATH_POLSKA,
        "geom_2180",
        {"id": "Int64", "typ": "string", "geom_2180": "string"},
    )

    poi = load_gdf(
        PATH_POI,
        "geom_point_2180",
        {"id": "Int64", "category": "string", "geom_point_2180": "string"},
    )

    geo_polska["typ"] = geo_polska["typ"].astype("category")
    poi["category"] = poi["category"].astype("category")

    experiment_5_geom_features(geo_polska)
    experiment_6_buffer_intersection(geo_polska)
    experiment_7_sjoin(poi, geo_polska)
    experiment_8_voronoi(geo_polska, poi)

    print("\nEksperymenty 5–8 zakończone poprawnie.")
