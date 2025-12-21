function mToRad(m) { return m / 6378137; }

var start = new Date();

// 0) Definicja promieni buforów w metrach
const radii = {
    cnt_50m: 50,
    cnt_100m: 100,
    cnt_500m: 500,
    cnt_1000m: 1000,
    cnt_5000m: 5000,
    cnt_50000m: 50000,
    cnt_100000m: 100000
};

// 1) Definicja punktu referencyjnego
const ref = {
    type: "Point",
    coordinates: [19.46701915338524, 51.74357018348951]
};

// 2) Pobranie kategorii
const categories = db.dat_poi.distinct("category", { category: { $ne: null } });

// 3) Pętla licząca liczbę POI w każdym buforze
var results = [];

categories.forEach(cat => {

    let rec = { category: cat };

    for (const key in radii) {
        rec[key] = db.dat_poi.countDocuments({
            category: cat,
            geom_point_4326: {
                $geoWithin: {
                    $centerSphere: [
                        ref.coordinates,
                        mToRad(radii[key])
                    ]
                }
            }
        });
    }

    results.push(rec);
});

var end = new Date();

print("CZAS EKSPERYMENTU 3 — JEDNA WARTOŚĆ (ms):", end - start);
printjson(results);
