import geopandas as gpd
from geopandas.tools import sjoin
import pandas as pd
import osm_split
import osm_extract

buffer_size = 0.00001

# read shapefiles
# tunnels, bridges, roads = osm_extract.read_road_sf()
print("start reading roads file")
# roads = gpd.read_file(r"OSM_shp\\roads.shp").to_crs(2855)
# print("start reading bridges file")
# bridges = gpd.read_file(r'OSM_shp\\bridges.shp').to_crs(2855)
# print("start reading tunnels file")
# tunnels = gpd.read_file(r'OSM_shp\\tunnels.shp').to_crs(2855)


tunnels, bridges, roads = osm_extract.read_road_sf()

# change corrdinates
tunnels = tunnels.to_crs(2855)
bridges = bridges.to_crs(2855)
roads = roads.to_crs(2855)

# split all sfs
print("start splitting tunnels")


link1, no_join, dup1 = osm_split.split(tunnels)
link, tunnels_dup = osm_split.join_buffer(tunnels, no_join, link1, buffer_size)
link.to_file(r'test_results\\tunnels_link2.shp')
print("tunnel duplicates")
print(tunnels_dup)


print("start splitting bridges")
link1, no_join, dup1 = osm_split.split(bridges)
link, bridges_dup = osm_split.join_buffer(bridges, no_join, link1, buffer_size)
link.to_file(r'test_results\\bridges_link2.shp')
print("bridge duplicates")
print(bridges_dup)


print("start splitting roads")
link1, no_join, dup1 = osm_split.split(roads  )
link, roads_dup = osm_split.join_buffer(roads, no_join, link1, buffer_size)
link.to_file(r'test_results\\roads_link2.shp')
print("road duplicates")
print(roads_dup)
