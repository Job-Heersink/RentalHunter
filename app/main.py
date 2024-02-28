import asyncio

from app.scraper import scrape


async def main():
    new_df = await scrape()
    new_df.to_csv("houses.csv")


def handler(event, context):
    asyncio.run(main())


if __name__ == '__main__':
    handler(None, None)
