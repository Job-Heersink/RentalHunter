import asyncio
import logging
import time

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.sites import site_list


def task_to_result(tasks):
    for t in tasks:
        r = t.result()
        if r is not None:
            for house in r:
                yield house.dict()


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