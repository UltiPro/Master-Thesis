CREATE OR REPLACE TABLE `mgr-2025.mgr_2025.geo_polska_geom_features` AS
SELECT
    id,
    nazwa,
    typ,

    -- powierzchnia w m²
    ST_AREA(geom_4326) AS area_m2,

    -- długość granicy w metrach
    ST_PERIMETER(geom_4326) AS perimeter_m,

    -- centroid GEOGRAPHY (współrzędne geograficzne)
    ST_CENTROID(geom_4326) AS centroid_4326

FROM `mgr-2025.mgr_2025.geo_polska`;
