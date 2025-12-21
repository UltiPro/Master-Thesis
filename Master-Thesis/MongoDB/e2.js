var start = new Date();

var results = [];

var refPoint = {
    type: "Point",
    coordinates: [19.46701915338524, 51.74357018348951]  // WGS84
};

var categories = db.dat_poi.distinct("category").filter(c => c != null);

categories.forEach(cat => {

    // pobranie najbliższego obiektu + odległości w jednym pipeline
    const nearestDocs = db.dat_poi.aggregate([
        {
            $geoNear: {
                near: refPoint,
                distanceField: "dist",
                spherical: true,
                query: { category: cat },
            }
        },
        { $limit: 1 }
    ]).toArray();

    if (nearestDocs.length > 0) {
        const nearest = nearestDocs[0];
        results.push({
            category: cat,
            nearest_poi_id: nearest.id,
            distance_m: nearest.dist
        });
    }
});

var end = new Date();

print("\nCzas wykonania EKSPERYMENTU 2 (ms):", end - start);
print("\nWyniki:");
printjson(results);
