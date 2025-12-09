import geopandas as gpd
import shapely
import pyproj
import rtree
import pandas as pd
import numpy as np

print("GeoPandas:", gpd.__version__)
print("Shapely:", shapely.__version__)
print("GEOS version (from Shapely):", shapely.geos_version)
print("pyproj:", pyproj.__version__)
print("Rtree:", rtree.__version__)
print("Pandas:", pd.__version__)
print("NumPy:", np.__version__)
