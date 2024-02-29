import asyncio
from datetime import datetime
import logging


import pandas as pd

from app.data_handler import get_houses, put_houses, get_subscribers
from app.geocoding import get_geocode
from app.scraper import scrape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_geocode_for_df(df, address):
    row = df.loc[address]
    if row["lat"] is not None and row["lon"] is not None:
        return

    pos = await get_geocode(row["address"], row["city"])
    logger.info(f"Geocoded {row['address']}, {row['city']}: {pos}")

    df.loc[address, ["lat", "lon"]] = pos


async def main():
    scrape_start = datetime.now()

    #old_df = await get_houses()
    #new_df = pd.read_csv("temp.csv", index_col="address")
    new_df, old_df, subs = await asyncio.gather(scrape(), get_houses(), get_subscribers())
    new_df["scrape_date"] = pd.to_datetime(new_df['scrape_date'])
    old_df["scrape_date"] = pd.to_datetime(old_df['scrape_date'])
    #new_df.head(-10).to_csv("temp.csv")

    await put_houses(pd.concat([new_df, old_df]).drop_duplicates(keep="last"))
    new_df = pd.concat([new_df, old_df]).drop_duplicates(keep=False)
    new_df = new_df.loc[new_df["scrape_date"] >= scrape_start]

    print(new_df)
    await asyncio.gather(*[get_geocode_for_df(new_df, address) for address in new_df.head(5).index])

    # for s in subs.iterrows():
    #     for i, row in new_df.iterrows():
    #         if s["city"] == row["city"]:
    #             print(f"Sending mail to {s['email']} for {row['address']}")
    #             # send_mail(s["email"], row)




def handler(event, context):
    asyncio.run(main())


if __name__ == '__main__':
    handler(None, None)
