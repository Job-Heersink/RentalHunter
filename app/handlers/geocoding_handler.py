import logging
import os

from opencage.geocoder import OpenCageGeocode, RateLimitExceededError

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEOCODING_API_KEY")
geocoder = OpenCageGeocode(API_KEY)


def get_lon_lat(address: str, city, country="Netherlands") -> dict:
    try:
        result = geocoder.geocode(",".join([address, city, country]))
        if result and len(result):
            return result[0]['geometry']
    except RateLimitExceededError as ex:
        logger.error(f"Rate limit exceeded: {ex}")
        raise ex
