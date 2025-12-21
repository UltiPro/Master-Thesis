// Usuń poprzednie wyniki
db.vw_hex_poi_counts_mongo.drop();

var start = new Date();

// Pobierz 1000000 hexów
const hexes = db.geo_hex
    .find({})
    .limit(1000000)
    .toArray();

// Przetwarzanie każdego hexagonu
hexes.forEach((h, i) => {

    // policz punkty POI w wielokącie
    const count = db.dat_poi.countDocuments({
        geom_point_4326: {
            $geoWithin: {
                $geometry: h.geom_4326
            }
        }
    });

    // zapis wyniku
    db.vw_hex_poi_counts_mongo.insertOne({
        hex_0125: h.hex_0125,
        poi_count: count
    });
});

var end = new Date();

print("\nEksperyment 14 — czas całkowity (ms):", end - start);
print("Wyniki zapisano w kolekcji: vw_hex_poi_counts_mongo");
