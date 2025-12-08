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
-- dat_poi_mdb.csv 
-- Measure time taken for import
Measure-Command {
    mongoimport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=dat_poi `
        --type=csv `
        --headerline `
        --file="C:/Users/Ultip/Desktop/mgr/mdb/dat_poi_mdb.csv"
}

-----------------------------------------
-- geo_polska_mdb.csv
-- Measure time taken for import
Measure-Command {
    mongoimport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=geo_polska `
        --type=csv `
        --headerline `
        --file="C:/Users/Ultip/Desktop/mgr/mdb/geo_polska_mdb.csv"
}

-----------------------------------------
-- osm_roads_mdb.csv
-- Measure time taken for import
Measure-Command {
    mongoimport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=osm_roads `
        --type=csv `
        --headerline `
        --file="C:/Users/Ultip/Desktop/mgr/mdb/osm_roads_mdb.csv"
}

-----------------------------------------
-- geo_hex_mdb.csv
-- Measure time taken for import
Measure-Command {
    mongoimport `
        --uri="mongodb://localhost:27017" `
        --db=mgr_mongo `
        --collection=geo_hex `
        --type=csv `
        --headerline `
        --file="C:/Users/Ultip/Desktop/mgr/mdb/geo_hex_mdb.csv"
}
