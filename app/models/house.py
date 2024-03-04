from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, Field


class House(BaseModel):
    link: str
    source: str
    city: str
    address: str
    available: bool = True
    square_meters: Optional[float] = None
    bedrooms: Optional[int] = None

    price: Optional[float] = None

    lat: Optional[float] = None
    lon: Optional[float] = None
    postalcode: Optional[str] = None

    scrape_date: datetime = Field(default_factory=datetime.now)

    @classmethod
    @field_validator('city')
    def capitalize_city(cls, v: str) -> str:
        return v.capitalize()


