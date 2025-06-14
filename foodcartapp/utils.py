import requests
from geopy.distance import distance as geopy_distance
from django.conf import settings
from places.models import Place

def fetch_coordinates(address):
    place, created = Place.objects.get_or_create(address=address)

    if place.latitude and place.longitude:
        return place.latitude, place.longitude

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": settings.YANDEX_GEOCODER_API_KEY,
        "geocode": address,
        "format": "json",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        geo_data = response.json()
        geo_object = geo_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
        lon, lat = map(float, geo_object['Point']['pos'].split())
        place.latitude = lat
        place.longitude = lon
        place.save()
        return lat, lon
    except (KeyError, IndexError, ValueError, requests.RequestException):
        return None


def get_distance_km(from_coords, to_coords):
    return round(geopy_distance(from_coords, to_coords).km, 2)
