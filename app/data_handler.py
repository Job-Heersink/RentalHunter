import logging
import os

import aioboto3
import pandas as pd
import uuid

logger = logging.getLogger(__name__)

session = aioboto3.Session()
data_bucket = os.getenv("DATA_BUCKET")
house_key = os.getenv("HOUSES_KEY")
subscribers_key = os.getenv("SUBSCRIBERS_KEY")

assert data_bucket is not None


async def _get(key, **kwargs):
    async with session.client("s3") as s3:
        os.makedirs("/tmp", exist_ok=True)
        tmp_file = f"/tmp/{uuid.uuid4()}.csv"
        await s3.download_file(data_bucket, key, tmp_file)
        logger.info(f"Downloaded {key}")
        return pd.read_csv(tmp_file, **kwargs)


async def _put(key, df):
    async with session.client("s3") as s3:
        os.makedirs("/tmp", exist_ok=True)
        tmp_file = f"/tmp/{uuid.uuid4()}.csv"
        df.to_csv(tmp_file)
        logger.info(f"Uploaded {key}")
        await s3.upload_file(tmp_file, data_bucket, key)


async def get_houses():
    return await _get(house_key, index_col="address")


async def get_subscribers():
    return await _get(subscribers_key)


async def put_houses(df):
    await _put(house_key, df)


async def put_subscribers(df):
    await _put(subscribers_key, df)
