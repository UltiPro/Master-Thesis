# --- WARM-UP (rozgrzewka narzędzi i połączenia) ---
mongoimport `
    --uri="mongodb://localhost:27017" `
    --db=mgr_mongo `
    --collection=warmup_dummy `
    --type=csv `
    --headerline `
    --file="C:/Users/Ultip/Desktop/mgr/dat_poi.csv" `
    --numInsertionWorkers=1 `
    --drop `
    | Out-Null

-----------------------------------------
Measure-Command {
    mongoexport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=dat_poi `
        --type=csv `
        --fields=id,osm_id,name_brand,name_brand_clean,name,name_clean,source_name,category,geom_point_4326 `
        --out="C:/Users/Ultip/Desktop/mgr/mdb/export_dat_poi_mongo.csv"
}

-----------------------------------------
Measure-Command {
    mongoexport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=geo_polska `
        --type=csv `
        --fields=id,typ,nazwa,teryt7,woj,pow,gmi,rodz_gmi,geom_4326 `
        --out="C:/Users/Ultip/Desktop/mgr/mdb/export_geo_polska_mongo.csv"
}

-----------------------------------------
Measure-Command {
    mongoexport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=osm_roads `
        --type=csv `
        --fields=id,osm_id,highway,geom_line_4326 `
        --out="C:/Users/Ultip/Desktop/mgr/mdb/export_osm_roads_mongo.csv"
}

-----------------------------------------
Measure-Command {
    mongoexport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=geo_hex `
        --type=csv `
        --fields=hex_0125,teryt7,woj,pow,gmi,geom_4326 `
        --out="C:/Users/Ultip/Desktop/mgr/mdb/export_geo_hex_mongo.csv"
}
