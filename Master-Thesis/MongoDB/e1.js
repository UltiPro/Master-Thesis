var start = new Date();

var result = db.dat_poi.find({
  geom_point_4326: {
    $nearSphere: {
      $geometry: {
        type: "Point",
        coordinates: [19.46701915338524, 51.74357018348951]
      },
    }
  }
})
  .limit(1)
  .toArray();

var end = new Date();

print("Wynik:", JSON.stringify(result, null, 2));
print("Czas wykonania (ms):", end - start);
