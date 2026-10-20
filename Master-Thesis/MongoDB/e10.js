// Czyszczenie wyników
db.feat_poi_nearest_road.drop();

// START POMIARU CZASU
const t0 = Date.now();

let processed = 0;

// Pobranie próby POI
const poiCursor = db.dat_poi.find(
    {
        "geom_point_4326.type": "Point",
        "geom_point_4326.coordinates": { $type: "array", $size: 2 }
    },
    {
        id: 1,
        geom_point_4326: 1
    }
).limit(1000000);

// Iteracyjne wyszukiwanie najbliższej drogi
poiCursor.forEach(poi => {

    const coords = poi.geom_point_4326.coordinates;

    const nearestRoad = db.osm_roads.aggregate([
        {
            $geoNear: {
                near: {
                    type: "Point",
                    coordinates: coords
                },
                key: "geom_line_4326",
                distanceField: "distance_m",
                spherical: true
            }
        },
        { $limit: 1 },
        {
            $project: {
                _id: 0,
                poi_id: { $literal: poi.id },
                road_id: "$id",
                distance_m: 1
            }
        }
    ]).toArray();

    if (nearestRoad.length > 0) {
        if (processed === 0) {
            print("Pierwszy wynik:", nearestRoad[0]);
        }
        db.feat_poi_nearest_road.insertOne(nearestRoad[0]);
        processed++;
    }
});

// STOP POMIARU CZASU
const t1 = Date.now();

// RAPORT
print("=======================================");
print("Eksperyment 10 - MongoDB");
print("POI przetworzone:", processed);
print("Czas całkowity [ms]:", t1 - t0);
print("Czas całkowity [s]:", ((t1 - t0) / 1000).toFixed(3));
print("=======================================");
