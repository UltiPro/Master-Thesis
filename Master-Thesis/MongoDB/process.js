use mgr_mongo;

//----------------------------------------------------
// FUNKCJA: konwersja JSON-string → obiekt GeoJSON + indeks
//----------------------------------------------------
function processGeometry(collectionName, geomField) {
    print("\n===========================================");
    print("   PRZETWARZANIE KOLEKCJI:", collectionName);
    print("   Pole geometrii:", geomField);
    print("===========================================\n");

    // -------------------------
    // 1) Konwersja JSON.parse()
    // -------------------------
    var start = new Date();

    db[collectionName].updateMany(
        {},
        [
            {
                $set: {
                    [geomField]: {
                        $function: {
                            body: function (x) {
                                try { return JSON.parse(x); }
                                catch (e) { return null; }
                            },
                            args: [`$${geomField}`],
                            lang: "js"
                        }
                    }
                }
            }
        ]
    );

    var end = new Date();
    print(collectionName, "--- czas konwersji JSON → Object (ms):", end - start);

    // -------------------------
    // 2) Indeks przestrzenny 2dsphere
    // -------------------------
    start = new Date();
    db[collectionName].createIndex({ [geomField]: "2dsphere" });
    end = new Date();

    print(collectionName, "--- czas tworzenia indeksu 2dsphere (ms):", end - start);

    print("\n✔ Zakończono:", collectionName, "\n");
}

//----------------------------------------------------
// PREPROCESSING GEOMETRII
//----------------------------------------------------

// dat_poi – Point
processGeometry("dat_poi", "geom_point_4326");

// geo_polska – MultiPolygon
processGeometry("geo_polska", "geom_4326");

// osm_roads – MultiLineString
processGeometry("osm_roads", "geom_line_4326");

// geo_hex – MultiPolygon
processGeometry("geo_hex", "geom_4326");

//----------------------------------------------------
// INDEKSY ATRYBUTOWE (DODATKOWE)
//----------------------------------------------------

print("\n===========================================");
print("   TWORZENIE INDEKSÓW ATRYBUTOWYCH");
print("===========================================\n");

var start, end;

// dat_poi → category
start = new Date();
db.dat_poi.createIndex({ category: 1 });
end = new Date();
print("dat_poi --- indeks category (ms):", end - start);

// geo_polska → typ
start = new Date();
db.geo_polska.createIndex({ typ: 1 });
end = new Date();
print("geo_polska --- indeks typ (ms):", end - start);

// osm_roads → highway
start = new Date();
db.osm_roads.createIndex({ highway: 1 });
end = new Date();
print("osm_roads --- indeks highway (ms):", end - start);

print("\n=== PREPROCESSING + INDEKSY ZAKOŃCZONE ===\n");
