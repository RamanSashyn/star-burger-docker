import requests
from geopy.distance import distance as geopy_distance
from django.conf import settings

def fetch_coordinates(address):
    apikey = settings.YANDEX_GEOCODER_API_KEY
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": apikey, "geocode": address, "format": "json"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        geo_object = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
        lon, lat = map(float, geo_object['Point']['pos'].split(' '))
        return lat, lon
    except (IndexError, KeyError, ValueError):
        return None

def get_distance_km(from_coords, to_coords):
    return round(geopy_distance(from_coords, to_coords).km, 2)
