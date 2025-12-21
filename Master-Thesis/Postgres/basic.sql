-- schema creation
CREATE SCHEMA IF NOT EXISTS mgr_2025;

-- extensions creation
CREATE EXTENSION IF NOT EXISTS postgis SCHEMA public;

-- dat_poi table
DROP TABLE IF EXISTS mgr_2025.dat_poi;
CREATE TABLE mgr_2025.dat_poi (
    id INTEGER,
    osm_id BIGINT,
    name_brand VARCHAR(255),
    name_brand_clean VARCHAR(255),
    name VARCHAR(255),
    name_clean VARCHAR(255),
    source_name VARCHAR(100),
    category VARCHAR(100),

    -- kolumna pomocnicza do importu WKT z CSV
    geom_wkt TEXT,

    -- geometrie właściwe (uzupełniane po imporcie)
    geom_point_4326 geometry(Point, 4326),
    geom_point_2180 geometry(Point, 2180),

    CONSTRAINT dat_poi_pkey PRIMARY KEY (id)
);

-- geo_polska table
DROP TABLE IF EXISTS mgr_2025.geo_polska;
CREATE TABLE mgr_2025.geo_polska (
    id INTEGER,
    typ VARCHAR(50),
    nazwa VARCHAR(100),
    teryt7 VARCHAR(7),
    woj VARCHAR(2),
    pow VARCHAR(2),
    gmi VARCHAR(2),
    rodz_gmi VARCHAR(1),

    -- WKT z CSV (MultiPolygon)
    geom_wkt TEXT,

    -- geometrie właściwe
    geom_4326 geometry(MultiPolygon, 4326),
    geom_2180 geometry(MultiPolygon, 2180),

    CONSTRAINT geo_polska_pkey PRIMARY KEY (id)
);

-- osm_roads table
DROP TABLE IF EXISTS mgr_2025.osm_roads;
CREATE TABLE mgr_2025.osm_roads (
    id BIGINT,
    osm_id BIGINT,
    highway VARCHAR(50),
    -- WKT z CSV
    geom_wkt TEXT,

    -- geometria liniowa
    geom_line_4326 geometry(MultiLineString, 4326),
    geom_line_2180 geometry(MultiLineString, 2180),

    CONSTRAINT osm_roads_pkey PRIMARY KEY (id)
);

-- geo_hex table
DROP TABLE IF EXISTS mgr_2025.geo_hex;
CREATE TABLE mgr_2025.geo_hex (
    hex_0125 BIGINT,
    teryt7 VARCHAR(7),
    woj VARCHAR(100),
    pow VARCHAR(100),
    gmi VARCHAR(100),

    -- WKT polygons + centroid z CSV
    geom_wkt TEXT,

    -- geometrie właściwe
    geom_4326 geometry(MultiPolygon, 4326),
    geom_2180 geometry(MultiPolygon, 2180),

    CONSTRAINT geo_hex_pkey PRIMARY KEY (hex_0125)
);

-- DAT_POI TABLE IMPORT SCRIPT
-- Wczytanie dat_poi z CSV z geometrią w 4326 (WKT)
COPY mgr_2025.dat_poi (
    id,
    osm_id,
    name_brand,
    name_brand_clean,
    name,
    name_clean,
    source_name,
    category,
    geom_wkt
)
FROM 'C:\Users\Ultip\Desktop\mgr\dat_poi.csv'
DELIMITER ','
CSV HEADER;

-- Ustawienie SRID dla kolumny geom_point_4326 na 4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.dat_poi
SET geom_point_4326 = ST_SetSRID(ST_GeomFromText(geom_wkt), 4326)
WHERE geom_wkt IS NOT NULL;

-- Usunięcie kolumny pomocniczej geom_wkt
ALTER TABLE mgr_2025.dat_poi
DROP COLUMN geom_wkt;

-- Naprawa niepoprawnych geometrii w kolumnie geom_point_4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.dat_poi
SET geom_point_4326 = ST_MakeValid(geom_point_4326)
WHERE NOT ST_IsValid(geom_point_4326);

-- Conwersja geometrii punktowej z 4326 do 2180
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.dat_poi
SET geom_point_2180 = ST_Transform(geom_point_4326, 2180);

-- Indeks przestrzenny dla kolumny geom_point_2180
CREATE INDEX idx_dat_poi_geom_point_2180
ON mgr_2025.dat_poi
USING GIST (geom_point_2180);

-- Eksport tabeli dat_poi do CSV z geometrią w WKT
COPY (
    SELECT
        id,
        osm_id,
        name_brand,
        name_brand_clean,
        name,
        name_clean,
        source_name,
        category,
        ST_AsText(geom_point_4326)
    FROM mgr_2025.dat_poi
)
TO 'C:\Program Files\PostgreSQL\18\data\export_dat_poi.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- GEO_POLSKA TABLE IMPORT SCRIPT
-- Wczytanie geo_polska z CSV z geometrią w 4326 (WKT)
COPY mgr_2025.geo_polska (
    id,
    typ,
    nazwa,
    teryt7,
    woj,
    pow,
    gmi,
    rodz_gmi,
    geom_wkt
)
FROM 'C:\Users\Ultip\Desktop\mgr\geo_polska.csv'
DELIMITER ','
CSV HEADER;

-- Ustawienie SRID dla kolumny geom_4326 na 4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_polska
SET geom_4326 = ST_SetSRID(ST_GeomFromText(geom_wkt), 4326)
WHERE geom_wkt IS NOT NULL;

-- Usunięcie kolumny pomocniczej geom_wkt
ALTER TABLE mgr_2025.geo_polska
DROP COLUMN geom_wkt;

-- Naprawa niepoprawnych geometrii w kolumnie geom_4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_polska
SET geom_4326 = ST_MakeValid(geom_4326)
WHERE NOT ST_IsValid(geom_4326);

-- Transformacja geometrii polygon z 4326 do 2180
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_polska
SET geom_2180 = ST_Transform(geom_4326, 2180);

-- Indeks przestrzenny dla kolumny geom_4326
CREATE INDEX idx_geo_polska_geom_2180
ON mgr_2025.geo_polska
USING GIST (geom_2180);

-- Eksport tabeli dat_poi do CSV z geometrią w WKT
COPY (
    SELECT
        id,
        typ,
        nazwa,
        teryt7,
        woj,
        pow,
        gmi,
        rodz_gmi,
        ST_AsText(geom_4326)
    FROM mgr_2025.geo_polska
)
TO 'C:\Program Files\PostgreSQL\18\data\export_geo_polska.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- OSM_ROADS TABLE IMPORT SCRIPT
-- Wczytanie osm_roads z CSV z geometrią w 4326 (WKT)
COPY mgr_2025.osm_roads (
    id,
    osm_id,
    highway,
    geom_wkt
)
FROM 'C:\Users\Ultip\Desktop\mgr\dat_roads.csv'
DELIMITER ','
CSV HEADER;

-- Ustawienie SRID dla kolumny geom_line_4326 na 4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.osm_roads
SET geom_line_4326 = ST_SetSRID(ST_GeomFromText(geom_wkt), 4326)
WHERE geom_wkt IS NOT NULL;

-- Usunięcie kolumny pomocniczej geom_wkt
ALTER TABLE mgr_2025.osm_roads
DROP COLUMN geom_wkt;

-- Naprawa niepoprawnych geometrii w kolumnie geom_line_4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.osm_roads
SET geom_line_4326 = ST_MakeValid(geom_line_4326)
WHERE NOT ST_IsValid(geom_line_4326);

-- Conwersja geometrii liniowej z 4326 do 2180
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.osm_roads
SET geom_line_2180 = ST_Transform(geom_line_4326, 2180);

-- Indeks przestrzenny dla kolumny geom_line_4326
CREATE INDEX idx_osm_roads_geom_line_2180
ON mgr_2025.osm_roads
USING GIST (geom_line_2180);

-- Eksport tabeli osm_roads do CSV z geometrią w WKT
COPY (
    SELECT
        id,
        osm_id,
        highway,
        ST_AsText(geom_line_4326)
    FROM mgr_2025.osm_roads
)
TO 'C:\Program Files\PostgreSQL\18\data\export_osm_roads.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- GEO_HEX TABLE IMPORT SCRIPT
-- Wczytanie geo_hex z CSV z geometrią w 4326 (WKT)
COPY mgr_2025.geo_hex (
    hex_0125,
    teryt7,
    woj,
    pow,
    gmi,
    geom_wkt
)
FROM 'C:\Users\Ultip\Desktop\mgr\geo_hex.csv'
DELIMITER ','
CSV HEADER;

-- Ustawienie SRID dla kolumny geom_4326 na 4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_hex
SET geom_4326 = ST_SetSRID(ST_GeomFromText(geom_wkt), 4326)
WHERE geom_wkt IS NOT NULL;

-- Usunięcie kolumny pomocniczej geom_wkt
ALTER TABLE mgr_2025.geo_hex
DROP COLUMN geom_wkt;

-- Naprawa niepoprawnych geometrii w kolumnie geom_4326
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_hex
SET geom_4326 = ST_MakeValid(geom_4326)
WHERE NOT ST_IsValid(geom_4326);

-- Conwersja geometrii z 4326 do 2180
EXPLAIN (ANALYZE, BUFFERS)
UPDATE mgr_2025.geo_hex
SET geom_2180 = ST_Transform(geom_4326, 2180);

-- Indeks przestrzenny dla kolumny geom_4326
CREATE INDEX idx_geo_hex_geom_2180
ON mgr_2025.geo_hex
USING GIST (geom_2180);

-- Eksport tabeli geo_hex do CSV z geometrią w WKT
COPY (
    SELECT
        hex_0125,
        teryt7,
        woj,
        pow,
        gmi,
        ST_AsText(geom_4326)
    FROM mgr_2025.geo_hex
)
TO 'C:\Program Files\PostgreSQL\18\data\export_geo_hex.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- category index
CREATE INDEX idx_dat_poi_category
ON mgr_2025.dat_poi (category);

-- highway index
CREATE INDEX idx_osm_roads_highway
ON mgr_2025.osm_roads (highway);

-- typ index
CREATE INDEX idx_geo_polska_typ
ON mgr_2025.geo_polska (typ);
