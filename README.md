# Master-Thesis
Master-Thesis created by Patryk 'UltiPro' Wójtowicz using PostgreSQL/PostGIS, DuckDB Spatial, GeoPandas, MongoDB and Google BigQuery.

This repository contains the source code of the experiments developed for my Master's Thesis at the Bialystok University of Technology (Faculty of Computer Science).

> ***Badanie wydajności wybranych silników obliczeniowych do przetwarzania danych przestrzennych w metrycznych układach odniesienia 2D***<br/>
> ***Performance testing of selected computational engines for processing spatial data in 2D metric reference systems***<br/>
> Author: Patryk Wójtowicz · Supervisor: dr inż. Tomasz Grześ · Bialystok University of Technology, 2026

The aim of the thesis was to compare the performance of selected computational engines used for spatial data processing in two-dimensional metric reference systems (EPSG:2180), and — where required by technological limitations — in the geodetic model (EPSG:4326). The study focuses on spatial operations relevant to feature engineering in machine learning tasks, such as distance calculations, spatial filtering, nearest-neighbor queries, spatial joins and aggregations.

Every engine went through the same pipeline, as far as it supported each step: data import from CSV (WKT), SRID assignment, geometry validation, CRS transformation (EPSG:4326 → EPSG:2180), spatial index creation, 16 experiments and data export. Execution times were measured for every stage.

📄 The full thesis (in Polish) is available here: [Master-Thesis-Patryk-Wojtowicz.pdf](Master-Thesis-Patryk-Wojtowicz.pdf)

⚠️ Note:

> Input datasets are not included in this repository, their sources are listed in the Datasets section below. Paths in the scripts point to local directories used during the research.

# 🛠️ Engines

| Folder | Engine | Spatial model | Spatial index |
|---|---|---|---|
| `Postgres/` | PostgreSQL 18.1 + PostGIS 3.6 | `geometry`, EPSG:2180 (reference variant) | GiST |
| `Postgres_4326/` | PostgreSQL 18.1 + PostGIS 3.6 | `geography`, EPSG:4326 | GiST |
| `DuckDB/` | DuckDB 1.4.2 + Spatial | `GEOMETRY`, EPSG:2180 | R-tree |
| `GeoPandas/` | GeoPandas 1.1.1, Shapely 2.1.2, GEOS 3.13.1 | planar, EPSG:2180 | STRtree / `sindex` |
| `MongoDB/` | MongoDB 8.2.2 | GeoJSON, EPSG:4326 | `2dsphere` |
| `BigQuery/` | Google BigQuery GIS | `GEOGRAPHY`, EPSG:4326 | managed by the platform |

### 💻 Environment

| Component | Specification |
|---|---|
| CPU | AMD Ryzen 9 7900 (12 cores / 24 threads), 3.7–5.4 GHz |
| RAM | 32 GB DDR5 6000 MHz CL30 |
| Disk | Lexar NQ790 1 TB, M.2 PCIe Gen4 NVMe |
| OS | Windows 11 Pro 25H2 (no VMs or containers) |
| Python | 3.14.0 (pyproj 3.7.2, Rtree 1.4.1, Pandas 2.3.3, NumPy 2.3.5) |
| BigQuery | Google Cloud, on-demand, state as of 12.2025 |

Library versions can be printed with `DuckDB/version.py` and `GeoPandas/packages.py`.

# 🗂️ Datasets

| Table | Geometry | Objects | Source |
|---|---|--:|---|
| `dat_poi` | Point | 903,735 | [OpenStreetMap](https://www.openstreetmap.org) |
| `osm_roads` | LineString | 1,076,076 | [OpenStreetMap](https://www.openstreetmap.org) |
| `geo_polska` | Polygon | 2,876 | [PRG – GUGiK Geoportal](https://www.geoportal.gov.pl/dane/panstwowy-rejestr-granic) |
| `geo_hex` | Polygon | 30,943,061 | synthetic (generated hexagonal grid) |

`dat_poi` and `osm_roads` were taken directly from OpenStreetMap without additional filtering, and `geo_polska` from the State Register of Borders (PRG). `geo_hex` is a synthetic regular hexagonal grid covering Poland, generated for the performance tests, with cells 125 m wide (side 62.5 m, area ≈ 0.01 km²). The way it was generated does not affect the results, so any regular hexagonal grid of a similar resolution covering Poland can be used instead.

Map data © OpenStreetMap contributors, available under the [ODbL](https://www.openstreetmap.org/copyright). Administrative boundaries from the State Register of Borders (PRG), GUGiK.

# 🧪 Experiments

| # | Experiment | PG | DDB | GP | MDB | BQ |
|---|---|:-:|:-:|:-:|:-:|:-:|
| | **Distance and nearest neighbor** | | | | | |
| E1 | Nearest POI to a reference point | ✅ | ✅ | ✅ | ✅ | ✅ |
| E2 | Nearest POI of each category to a reference point | ✅ | ✅ | ✅ | ✅ | ✅ |
| E3 | POI count per category within radii 50 m – 100 km | ✅ | ✅ | ✅ | ✅ | ✅ |
| E4 | Distance from POI to commune / county / voivodeship / country boundary | ✅ | ✅ | ✅ | | ✅ |
| | **Geometric and topological** | | | | | |
| E5 | Area, perimeter and centroid of all administrative units | ✅ | ✅ | ✅ | | ✅ |
| E6 | Intersection of communes buffered by 5 km with voivodeships | ✅ | ✅ | ✅ | | ✅ |
| E7 | POI count in administrative units on 4 levels | ✅ | ✅ | ✅ | ✅ | ✅ |
| E8 | Voronoi diagram of POI intersected with voivodeships | ✅ | | ✅ | | |
| | **Linear objects** | | | | | |
| E9 | Average road segment length per `highway` class | ✅ | ✅ | ✅ | | ✅ |
| E10 | Nearest road for each POI | ✅ | ✅ | ✅ | ✅ | ✅ |
| E11 | Longest road segment per `highway` class | ✅ | ✅ | ✅ | | ✅ |
| E12 | Total road length within 500 m of POI | ✅ | ✅ | ✅ | | ✅ |
| | **Aggregations on a hexagonal grid** | | | | | |
| E13 | Union of 1,000,000 hexagons within voivodeships | ✅ | | ✅ | | ✅ |
| E14 | POI count per hexagon | ✅ | ✅ | ✅ | ✅ | ✅ |
| E15 | Total road length per hexagon | ✅ | ✅ | ✅ | | ✅ |
| E16 | Hexagon → voivodeship join with cell and intersection area | ✅ | ✅ | ✅ | | ✅ |

PG – PostgreSQL/PostGIS (`Postgres/` and `Postgres_4326/`), DDB – DuckDB, GP – GeoPandas, MDB – MongoDB, BQ – BigQuery. A missing mark means the experiment was not performed in that engine. Some runs required input limits (E10 in DuckDB and BigQuery, E14 in MongoDB and BigQuery).

📝 Note: DuckDB Spatial provides `ST_Union_Agg` and `ST_VoronoiDiagram`, so E8 and E13 could be implemented in DuckDB. They were not implemented in this research.

# 📊 Key findings

- The planar model (`geometry`, EPSG:2180) was faster than the geodetic one (`geography`, EPSG:4326) in most scenarios, and the gap grew with data size and query complexity.
- **PostgreSQL/PostGIS** offered the widest range of supported operations and stable performance, at the cost of relatively expensive preprocessing.
- **DuckDB Spatial** was very fast in local batch workloads, especially spatial joins and aggregations on simple geometries in EPSG:2180 (e.g. POI count in 30.9 M hexagons in 2.27 s). It was slower on complex polygons (E7, E16) and has no `geography` type.
- **GeoPandas** was best for exploration and prototyping features, and it was the fastest in some polygon operations (E6, E16), but everything has to fit in memory.
- **BigQuery GIS** often had low elapsed time, but a high slot time consumed. It suits one-off or periodic processing of very large datasets.
- **MongoDB** supports only a small set of spatial operations (6 of 16 experiments), which limits its usefulness for spatial feature engineering.
- The hexagonal grid experiments (E13–E16) were the most demanding: some engines could not finish them within available resources or needed input limits.

# 📁 Repository structure

Each engine folder follows the same convention:

| File | Purpose |
|---|---|
| `basic.sql` / `*_process.py` / `*_preprocess.py` | Preprocessing: data import, SRID assignment, geometry validation, CRS transformation, spatial indexes, export |
| `e1` … `e16` | Experiments E1–E16 (in GeoPandas grouped as `e1_4.py`, `e5_8.py`, `e9_12.py`) |
| `version.py` / `packages.py` | Library versions used in the research |
| `MongoDB/special_export_from_pg.sql` | Export from PostgreSQL with geometry as GeoJSON, used as MongoDB input |
| `MongoDB/import.sh`, `export.sh` | `mongoimport` / `mongoexport` commands (PowerShell syntax) |
| `diagram.py` | Preprocessing time chart (Fig. 5.2.2 in the thesis) |

The scripts document the exact queries and processing steps behind the results in the thesis. They are not a ready-to-run pipeline.

# 📄 License

The source code is available under the [MIT License](LICENSE). The thesis text is not covered by this license, all rights reserved.
