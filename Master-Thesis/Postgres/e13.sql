-- =====================================================================
-- UnaryUnion heksagonów w obrębie województw.
-- Limit na 1,000,000 hexagonów.
-- =====================================================================

DROP TABLE IF EXISTS mgr_2025.geo_hex_union_woj;

CREATE TABLE mgr_2025.geo_hex_union_woj AS
WITH woj AS (
    SELECT 
        id AS woj_id,
        geom_2180
    FROM mgr_2025.geo_polska
    WHERE typ = 'województwo'
),
hex_sample AS (
    SELECT 
        hex_0125,
        geom_2180
    FROM mgr_2025.geo_hex
    ORDER BY hex_0125
    LIMIT 1000000
)
SELECT
    w.woj_id,
    ST_UnaryUnion(ST_Collect(h.geom_2180)) AS geom_union
FROM woj w
JOIN hex_sample h
    ON ST_Intersects(h.geom_2180, w.geom_2180)
GROUP BY w.woj_id;
