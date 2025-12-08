function countPoiPerAdmin(adminCollection, poiCollection, resultCollection) {

    db[resultCollection].drop();

    const adminUnits = db[adminCollection].find().toArray();

    adminUnits.forEach(a => {
        const count = db[poiCollection].countDocuments({
            geom_point_4326: {
                $geoWithin: {
                    $geometry: a.geom_4326
                }
            }
        });

        db[resultCollection].insertOne({
            admin_id: a.id,
            admin_name: a.nazwa,
            admin_type: a.typ,
            poi_count: count
        });
    });
}

var start = new Date();

countPoiPerAdmin("geo_polska", "dat_poi", "feat_poi_per_admin_mongo");

var end = new Date();
print("Czas pełnego eksperymentu (ms):", end - start);
