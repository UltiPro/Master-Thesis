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
        ST_AsGeoJSON(geom_point_4326) as geom_point_4326
    FROM mgr_2025.dat_poi
)
TO 'C:\Program Files\PostgreSQL\18\data\export_dat_poi_f_mdb.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

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
        ST_AsGeoJSON(geom_4326) as geom_4326
    FROM mgr_2025.geo_polska
)
TO 'C:\Program Files\PostgreSQL\18\data\export_geo_polska_f_mdb.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- Eksport tabeli osm_roads do CSV z geometrią w WKT
COPY (
    SELECT
        id,
        osm_id,
        highway,
        ST_AsGeoJSON(geom_line_4326) as geom_line_4326
    FROM mgr_2025.osm_roads
)
TO 'C:\Program Files\PostgreSQL\18\data\export_osm_roads_f_mdb.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');

-- Eksport tabeli geo_hex do CSV z geometrią w WKT
COPY (
    SELECT
        hex_0125,
        teryt7,
        woj,
        pow,
        gmi,
        ST_AsGeoJSON(geom_4326) as geom_4326
    FROM mgr_2025.geo_hex
)
TO 'C:\Program Files\PostgreSQL\18\data\export_geo_hex_f_mdb.csv'
WITH (FORMAT CSV, HEADER TRUE, QUOTE '"');
