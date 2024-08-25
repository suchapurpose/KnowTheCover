import json
import csv

input_file = 'demo/myapp/static/js/country_boundaries_reduced.geojson'
output_file = 'demo/myapp/static/js/country_boundaries_reduced.tsv'

with open(input_file, 'r') as geojson_file:
    geojson_data = json.load(geojson_file)

with open(output_file, 'w', newline='') as tsv_file:
    writer = csv.writer(tsv_file, delimiter='\t')
    
    # Write the header
    header = list(geojson_data['features'][0]['properties'].keys()) + ['geometry']
    writer.writerow(header)
    
    # Write the data
    for feature in geojson_data['features']:
        row = list(feature['properties'].values()) + [json.dumps(feature['geometry'])]
        writer.writerow(row)