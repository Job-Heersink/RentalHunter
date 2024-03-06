import asyncio
import os
from datetime import datetime
from typing import Optional, List, Iterable

import aioboto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, field_validator, Field

from app.database.base import BaseTable, scan_all

HOUSES_TABLE = os.getenv("HOUSES_TABLE")

session = aioboto3.Session()


class House(BaseTable):
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


async def _add_house(house: House):
    async with session.client("dynamodb") as dynamo_db:
        try:
            await dynamo_db.put_item(
                TableName=HOUSES_TABLE,
                Item=house.to_table_item(),
                ConditionExpression='attribute_not_exists(address)')
            return house
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                return None


async def add_houses(houses: Iterable[House]):
    results = await asyncio.gather(*[_add_house(h) for h in houses])

    print(f"stored {len(results)} houses")
    return (h for h in results if h is not None)


async def get_existing_house_addresses():
    async for address in scan_all(TableName=HOUSES_TABLE,
                                  Select='SPECIFIC_ATTRIBUTES',
                                  ProjectionExpression='address'):
        yield address['address']['S']
