ALTER TABLE mgr_2025.dat_poi
ADD COLUMN geom_point_4326_geog geography(Point, 4326);

ALTER TABLE mgr_2025.geo_polska
ADD COLUMN geom_4326_geog geography(MultiPolygon, 4326);

ALTER TABLE mgr_2025.osm_roads
ADD COLUMN geom_line_4326_geog geography(MultiLineString, 4326);

ALTER TABLE mgr_2025.geo_hex
ADD COLUMN geom_4326_geog geography(MultiPolygon, 4326);

UPDATE mgr_2025.dat_poi
SET geom_point_4326_geog = geom_point_4326::geography;

UPDATE mgr_2025.geo_polska
SET geom_4326_geog = geom_4326::geography;

UPDATE mgr_2025.osm_roads
SET geom_line_4326_geog = geom_line_4326::geography;

UPDATE mgr_2025.geo_hex
SET geom_4326_geog = geom_4326::geography;

CREATE INDEX idx_dat_poi_geom_point_4326_geog
ON mgr_2025.dat_poi
USING GIST (geom_point_4326_geog);

CREATE INDEX idx_geo_polska_geom_4326_geog
ON mgr_2025.geo_polska
USING GIST (geom_4326_geog);

CREATE INDEX idx_osm_roads_geom_line_4326_geog
ON mgr_2025.osm_roads
USING GIST (geom_line_4326_geog);

CREATE INDEX idx_geo_hex_geom_4326_geog
ON mgr_2025.geo_hex
USING GIST (geom_4326_geog);
