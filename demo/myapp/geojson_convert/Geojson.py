import geopandas

shpfile = geopandas.read_file('~/Downloads/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp')
shpfile.to_file('country_boundaries.geojson', driver='GeoJSON')