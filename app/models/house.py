from typing import Optional

from pydantic import BaseModel, field_validator


class HouseModel(BaseModel):
    link: str
    source: str
    city: str
    address: str
    square_meters: Optional[float] = None
    bedrooms: Optional[int] = None

    price: Optional[float] = None

    available: bool

    lat: Optional[float] = None
    lon: Optional[float] = None
    postalcode: Optional[str] = None

    @classmethod
    @field_validator('city')
    def capitalize_city(cls, v: str) -> str:
        return v.capitalize()


