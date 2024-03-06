import logging
import os

import aioboto3

from app.database.base import BaseTable, scan_all

logger = logging.getLogger(__name__)

SUBSCRIBER_TABLE = os.getenv("SUBSCRIBERS_TABLE")

session = aioboto3.Session()


class Subscriber(BaseTable):
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


async def get_subscribers():
    async for sub in scan_all(TableName=SUBSCRIBER_TABLE,
                              Select='ALL_ATTRIBUTES'):
        yield Subscriber.from_table_item(sub)


async def add_subscriber(sub: Subscriber):
    async with session.client("dynamodb") as dynamo_db:
        await dynamo_db.put_item(
            TableName=SUBSCRIBER_TABLE,
            Item=sub.to_table_item(),
            # ReturnValues='NONE' | 'ALL_OLD' | 'UPDATED_OLD' | 'ALL_NEW' | 'UPDATED_NEW',
            ReturnConsumedCapacity='TOTAL',
        )


async def remove_subscriber(channel_id: str):
    async with session.client("dynamodb") as dynamo_db:
        await dynamo_db.delete_item(
            TableName=SUBSCRIBER_TABLE,
            Key={'channel_id': {'S': channel_id}}
        )
