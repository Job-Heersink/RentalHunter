import uuid
from typing import Tuple

from pydantic import BaseModel, Field


class Subscriber(BaseModel):
    channel_id: str

    min_price: float = 0.0
    max_price: float = 1000000.0
    min_rooms: int = 0
    max_rooms: int = 50
    min_sqm: float = 0.0
    max_sqm: float = 1000.0

    city: str = "Amsterdam"
    longitude: float = 4.8924534
    latitude: float = 52.3730796
    radius: float = 5.0


