import asyncio
import logging
import time
from datetime import datetime

import pandas as pd

from app.handlers.data_handler import get_houses, put_houses

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


async def main():
    scrape_start = datetime.now()

    # old_df = await get_houses()
    # new_df = pd.read_csv("temp.csv", index_col="address")
    new_df, old_df, subs = await asyncio.gather(scrape(), get_houses(), get_subscribers())
    new_df["scrape_date"] = pd.to_datetime(new_df['scrape_date'])
    old_df["scrape_date"] = pd.to_datetime(old_df['scrape_date'])
    new_df.to_csv("temp.csv")

    await put_houses(pd.concat([new_df, old_df]).drop_duplicates(keep="last"))
    new_df = pd.concat([new_df, old_df]).drop_duplicates(keep=False)
    new_df = new_df.loc[new_df["scrape_date"] >= scrape_start]

    for s in subs.iter_rows():
        for i, row in new_df.iterrows():
            if s["city"] == row["city"]:
                print(f"Sending mail to {s['email']} for {row['address']}")
                # send_mail(s["email"], row)


def handler(event, context):
    logger.info("Starting scraper")
    logger.info(event)
    logger.info("context")
    logger.info(context)
    return
    asyncio.run(main())


if __name__ == '__main__':
    handler(None, None)
