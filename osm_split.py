import geopandas as gpd
from geopandas.tools import sjoin

# roads_path = "C:\\Users\\JLin\\OneDrive - Puget Sound Regional Council\\Documents\\psrc_work_files\\OSM\\OSM_shp\\roads.shp"
# bridges_path = "C:\\Users\\JLin\\OneDrive - Puget Sound Regional Council\\Documents\\psrc_work_files\\OSM\\OSM_shp\\bridges.shp"
# tunnels_path = "C:\\Users\\JLin\\OneDrive - Puget Sound Regional Council\\Documents\\psrc_work_files\\OSM\\OSM_shp\\tunnels.shp"
buffer_size = 0.00001

# read shp files and add road IDs
def read_shp_files(path, projection):
    sf = gpd.read_file(path)
    sf = sf.to_crs(2855)

    road_id = [j for j in range(len(sf))]
    sf["road_id"] = road_id

    return sf


# road split + initial results (no buffer)
def split(split_sf):
    geom = [i for i in split_sf.geometry.unary_union]
    id = [j for j in range(len(geom))]
    unary = gpd.GeoDataFrame({"link_id":id,"geometry":geom}, crs="EPSG:2855")
    # join links back to roads to give them properties
    result =sjoin(unary, split_sf, how="left",op='within')

    # all links that are not joined back to the original roads
    link_no_join = result[result['road_id'].isnull()]

    # find list of all links that are duplicated in the process (because some roads are overlapping)
    link_dup = result[result["link_id"].duplicated()].values.tolist()

    return result, link_no_join, link_dup


# secondary results for links that did not join back to road in the initial results (join with buffer)
def join_buffer(split_sf, link_no_join, result, buffer_size):
    
    # create buffer with original shapefile
    sf_buf = split_sf.copy()
    sf_buf.geometry = sf_buf.geometry.buffer(buffer_size,cap_style=2) # flat buffer

    # join the links to the buffered roads
    result_buf = gpd.sjoin(link_no_join[["link_id","geometry"]], sf_buf, how="left", op="within")

    # combine the 2 results: original split (without those not successfully joined) + links joined with buffer
    result_links = result[~result['road_id'].isnull()].append(result_buf)
    result_links = result_links[["link_id", "road_id", "highway", "name",	"bridge", "tunnel", "oneway", "geometry"]].astype({"road_id": int})

    # find list of all links that are duplicated in the process
    link_dup = result_links[result_links["link_id"].duplicated()].values.tolist()

    return result_links, link_dup
    