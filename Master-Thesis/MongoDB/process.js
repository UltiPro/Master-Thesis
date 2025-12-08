//----------------------------------------------------
//   FINALNY PREPROCESSING GEOJSON — MONGOSH
//   Dla Magisterki Patryka Wójtowicza
//----------------------------------------------------

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
                            body: function(x) {
                                try { return JSON.parse(x); }
                                catch(e) { return null; }
                            },
                            args: [ `$${geomField}` ],
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
    // 2) Tworzenie indeksu 2dsphere
    // -------------------------
    start = new Date();
    db[collectionName].createIndex({ [geomField]: "2dsphere" });
    end = new Date();

    print(collectionName, "--- czas tworzenia indeksu (ms):", end - start);

    print("\n✔ Zakończono:", collectionName, "\n");
}

//----------------------------------------------------
// URUCHOMIENIE FUNKCJI DLA 4 TABEL
//----------------------------------------------------

// dat_poi – Point
processGeometry("dat_poi", "geom_point_4326");

// geo_polska – MultiPolygon
processGeometry("geo_polska", "geom_4326");

// osm_roads – MultiLineString
processGeometry("osm_roads", "geom_line_4326");

// geo_hex – MultiPolygon
processGeometry("geo_hex", "geom_4326");

print("\n=== PREPROCESSING ZAKOŃCZONY DLA WSZYSTKICH TABEL ===\n");
