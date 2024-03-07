import asyncio
import logging
import time
from datetime import datetime

from app.database.house import add_houses, get_existing_house_addresses, House
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
                yield house


async def insert_geocode_in_house(house: House):
    if house.lat is not None and house.lon is not None:
        return

    pos = await get_geocode(address=house.address, city=house.city)
    logger.info(f"Geocoded {house.address}, {house.city}: {pos}")
    house.lat, house.lon = pos


async def get_known_addresses():
    return {a async for a in get_existing_house_addresses()}


async def scrape():
    logger.info("Started scraping")
    t = time.time()
    tasks = []
    for site in site_list:
        tasks.append(asyncio.create_task(site.crawl()))

    await asyncio.gather(*tasks)
    logger.info(f"Scraping took {time.time() - t:.2f} seconds")

    return task_to_result(tasks)


async def run():
    houses, known_addresses = await asyncio.gather(scrape(), get_known_addresses())
    new_houses = [h for h in houses if h.address not in known_addresses]
    await asyncio.gather(add_houses(new_houses), *[insert_geocode_in_house(h) for h in new_houses])
    return new_houses
