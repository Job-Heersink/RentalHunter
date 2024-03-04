import asyncio
import logging
import time
from datetime import datetime

import pandas as pd

from app.handlers.data_handler import get_houses, put_houses, get_subscribers
from app.handlers.geocoding_handler import get_geocode


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from app.sites import site_list


def task_to_result(tasks):
    for t in tasks:
        r = t.result()
        if r is not None:
            for house in r:
                yield house.dict()


async def get_geocode_for_df(df, address):
    row = df.loc[address]
    city = row["city"]
    if not row[["lat", "lon"]].isnull().values.any():
        return

    pos = await get_geocode(address=address, city=city)
    logger.info(f"Geocoded {address}, {city}: {pos}")

    df.loc[address, ["lat", "lon"]] = pos


async def scrape():
    logger.info("Started scraping")
    t = time.time()
    tasks = []
    for site in site_list:
        tasks.append(asyncio.create_task(site.crawl()))

    await asyncio.gather(*tasks)
    logger.info(f"Scraping took {time.time() - t:.2f} seconds")

    df = pd.DataFrame(task_to_result(tasks))
    df = df.set_index("address")

    return df


async def run():
    scrape_start = datetime.now()

    # old_df = pd.read_csv("temp_old.csv", index_col="address")
    # new_df = pd.read_csv("temp_new.csv", index_col="address")
    new_df, old_df = await asyncio.gather(scrape(), get_houses())
    new_df["scrape_date"] = pd.to_datetime(new_df['scrape_date'])
    old_df["scrape_date"] = pd.to_datetime(old_df['scrape_date'])

    combined_df = pd.concat([new_df, old_df])
    combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
    new_houses = combined_df.loc[combined_df["scrape_date"] >= scrape_start]

    logger.info(f"Found {len(new_houses)} new houses")
    await asyncio.gather(put_houses(combined_df), *[get_geocode_for_df(new_houses, address) for address in new_houses.index])
    return new_houses


