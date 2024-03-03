import uuid
from typing import Tuple

from pydantic import BaseModel, Field


class Subscriber(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str

    price: Tuple[float, float] = (0.0, 1000000.0)
    square_meters: Tuple[float, float] = (0.0, 1000.0)
    bedrooms: Tuple[int, int] = (0, 50)

    center_position: Tuple[float, float] = (0.0, 0.0)
    radius: float = 0.0


