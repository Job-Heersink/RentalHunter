from typing import Optional

from pydantic import BaseModel, field_validator


class HouseModel(BaseModel):
    link: str
    source: str
    city: str
    address: str
    square_meters: Optional[float] = None

    price: Optional[float] = None

    available: bool

    lat: Optional[float] = None
    lon: Optional[float] = None

    @field_validator('city')
    @classmethod
    def capitalize_city(cls, v: str) -> str:
        return v.capitalize()


