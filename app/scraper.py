import asyncio
import logging
import time
from datetime import datetime

import pandas as pd

from app.discord.commands import discord_bot

from app.handlers.data_handler import get_houses, put_houses, get_subscribers

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
    if row["lat"] is not None and row["lon"] is not None:
        return

    pos = await get_geocode(row["address"], row["city"])
    logger.info(f"Geocoded {row['address']}, {row['city']}: {pos}")

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

    print(new_df)
    await asyncio.gather(*[get_geocode_for_df(new_df, address) for address in new_df.head(5).index])

    for s in subs.iter_rows():
        for i, row in new_df.iterrows():
            if s["city"] == row["city"]:
                print(f"Sending mail to {s['email']} for {row['address']}")
                # send_mail(s["email"], row)


def handler(event, context):
    logger.info("Starting scraper")
    logger.info(event)
    logger.info(f"source {event.get('source')}")
    logger.info(f"rawPath {event.get('rawPath')}")

    if event is not None and event.get("source") == "aws.events":
        logger.info("Scheduled event")
        # asyncio.run(main())
    elif event is not None and event.get("rawPath") == "/discord":
        logger.info("Discord event")
        response = asyncio.run(discord_bot.handle_message(event))
        logger.info(response)
        return response
    else:
        return {"statusCode": 400, "body": "Operation not allowed"}
