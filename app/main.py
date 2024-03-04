import asyncio
import logging

from app import scraper
from app.discord.commands import discord_bot
from app.notifier import notify_subscribers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def route(event):
    logger.info(f"received event {event}")
    logger.info(f"source {event.get('source')} path {event.get('rawPath')}")

    if event is not None and event.get("source") == "aws.events":
        logger.info("Scheduled event")
        new_houses = await scraper.run()
        await notify_subscribers(new_houses)
    elif event is not None and event.get("rawPath") == "/discord":
        logger.info("Discord event")
        response = await discord_bot.handle_message(event)
        logger.info(response)
        return response
    else:
        return {"statusCode": 400, "body": "Operation not allowed"}


def handler(event, context):
    return asyncio.run(route(event))


# if __name__ == '__main__':
#     handler({"source": "aws.events"}, None)
