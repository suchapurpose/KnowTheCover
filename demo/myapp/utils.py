# utils.py
import json
import os
from django.conf import settings

def load_country_codes():
    geojson_path = os.path.join(settings.BASE_DIR, 'myapp/static/js/country_boundaries.geojson')
    with open(geojson_path, 'r') as file:
        geojson_data = json.load(file)
    
    country_codes = {feature['properties']['ISO_A2'] for feature in geojson_data['features']}
    return country_codes
# Cache the country codes to avoid loading the file multiple times
COUNTRY_CODES = load_country_codes()