-- dat_poi Table Creation and Data Load
CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.dat_poi_raw`
(
    id INT64,
    osm_id INT64,
    name_brand STRING,
    name_brand_clean STRING,
    name STRING,
    name_clean STRING,
    source_name STRING,
    category STRING,
    geom_point_4326 STRING
);

LOAD DATA OVERWRITE `mgr-2025.mgr_2025.dat_poi_raw`
FROM FILES (
    format = 'CSV',
    uris = ['gs://mgr-2025/dat_poi.csv'],
    skip_leading_rows = 1,
    allow_quoted_newlines = TRUE
);

CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.dat_poi` AS
SELECT
    id,
    osm_id,
    name_brand,
    name_brand_clean,
    name,
    name_clean,
    source_name,
    category,
    SAFE.ST_GEOGFROMTEXT(geom_point_4326) AS geom_point_4326
FROM `mgr-2025.mgr_2025.dat_poi_raw`;

EXPORT DATA OPTIONS (
  uri = 'gs://mgr-2025/export/dat_poi_*.csv',
  format = 'CSV',
  overwrite = true,
  header = true,
  field_delimiter = ','
) AS
SELECT *
FROM `mgr-2025.mgr_2025.dat_poi`;

-- Dodanie klastrowania do tabeli dat_poi na podstawie kolumny category
CREATE TABLE `mgr-2025.mgr_2025.dat_poi_tmp`
CLUSTER BY category AS
SELECT *
FROM `mgr-2025.mgr_2025.dat_poi`;

-- Usuń starą tabelę
DROP TABLE `mgr-2025.mgr_2025.dat_poi`;

-- Zmień nazwę tabeli tymczasowej na właściwą
ALTER TABLE `mgr-2025.mgr_2025.dat_poi_tmp`
RENAME TO `dat_poi`;

-- geo_polska Table Creation and Data Load
CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_polska_raw`
(
    id INT64,
    typ STRING,
    nazwa STRING,
    teryt7 STRING,
    woj STRING,
    pow STRING,
    gmi STRING,
    rodz_gmi STRING,
    geom_4326 STRING
);

LOAD DATA OVERWRITE `mgr-2025.mgr_2025.geo_polska_raw`
FROM FILES (
    format = 'CSV',
    uris = ['gs://mgr-2025/geo_polska.csv'],
    skip_leading_rows = 1,
    allow_quoted_newlines = TRUE
);

CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_polska` AS
SELECT
    id,
    typ,
    nazwa,
    teryt7,
    woj,
    pow,
    gmi,
    rodz_gmi,
    SAFE.ST_GEOGFROMTEXT(geom_4326) AS geom_4326
FROM `mgr-2025.mgr_2025.geo_polska_raw`;

EXPORT DATA OPTIONS (
  uri = 'gs://mgr-2025/export/geo_polska_*.csv',
  format = 'CSV',
  overwrite = true,
  header = true,
  field_delimiter = ','
) AS
SELECT *
FROM `mgr-2025.mgr_2025.geo_polska`;

-- osm_roads Table Creation and Data Load
CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.osm_roads_raw`
(
    id INT64,
    osm_id INT64,
    highway STRING,
    geom_4326 STRING
);

LOAD DATA OVERWRITE `mgr-2025.mgr_2025.osm_roads_raw`
FROM FILES (
    format = 'CSV',
    uris = ['gs://mgr-2025/dat_roads.csv'],
    skip_leading_rows = 1,
    allow_quoted_newlines = TRUE
);

CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.osm_roads` AS
SELECT
    id,
    osm_id,
    highway,
    SAFE.ST_GEOGFROMTEXT(geom_line_4326) AS geom_line_4326
FROM `mgr-2025.mgr_2025.osm_roads_raw`;

EXPORT DATA OPTIONS (
  uri = 'gs://mgr-2025/export/osm_roads_*.csv',
  format = 'CSV',
  overwrite = true,
  header = true,
  field_delimiter = ','
) AS 
SELECT *
FROM `mgr-2025.mgr_2025.osm_roads`;

-- Dodanie klastrowania do tabeli osm_roads na podstawie kolumny highway
CREATE TABLE `mgr-2025.mgr_2025.osm_roads_tmp`
CLUSTER BY highway AS
SELECT *
FROM `mgr-2025.mgr_2025.osm_roads`;

-- Usuń starą tabelę
DROP TABLE `mgr-2025.mgr_2025.osm_roads`;

-- Zmień nazwę tabeli tymczasowej na docelową
ALTER TABLE `mgr-2025.mgr_2025.osm_roads_tmp`
RENAME TO `osm_roads`;

-- geo_hex Table Creation and Data Load
CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_hex_raw`
(
    hex_0125 INT64,
    teryt7 STRING,
    woj STRING,
    pow STRING,
    gmi STRING,
    geom_4326 STRING
);

LOAD DATA OVERWRITE `mgr-2025.mgr_2025.geo_hex_raw`
FROM FILES (
    format = 'CSV',
    uris = ['gs://mgr-2025/geo_hex.csv'],
    skip_leading_rows = 1,
    allow_quoted_newlines = TRUE
);

CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_hex` AS
SELECT
    hex_0125,
    teryt7,
    woj,
    pow,
    gmi,
    SAFE.ST_GEOGFROMTEXT(geom_4326) AS geom_4326
FROM `mgr-2025.mgr_2025.geo_hex_raw`;

-- only partial export due to BigQuery export limits
EXPORT DATA OPTIONS (
  uri = 'gs://mgr-2025/export/geo_hex_*.csv',
  format = 'CSV',
  overwrite = true,
  header = true,
  field_delimiter = ','
) AS
SELECT *
FROM `mgr-2025.mgr_2025.geo_hex`;
